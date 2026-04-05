(function () {
  const cfg = window.DEKERSHIP_CFG;
  let ws;
  let sessionToken = cfg.token;
  let allowReconnect = true;

  const statusText = document.getElementById("statusText");
  const roomNameInput = document.getElementById("roomName");
  const roomsBody = document.getElementById("roomsBody");

  function send(event, payload) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return;
    }
    ws.send(JSON.stringify({ event, payload: payload || {} }));
  }

  function setStatus(text) {
    statusText.textContent = text;
  }

  function navigate(url) {
    allowReconnect = false;
    if (ws) {
      ws.close();
    }
    window.location.href = url;
  }

  function renderRooms(rooms) {
    roomsBody.innerHTML = "";
    if (!rooms.length) {
      roomsBody.innerHTML = '<tr><td colspan="3">Nenhuma sala aberta.</td></tr>';
      return;
    }

    for (const room of rooms) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${room.name}</td>
        <td>${room.players}/2</td>
        <td><button class="btn" data-room-id="${room.room_id}">Entrar</button></td>
      `;
      roomsBody.appendChild(tr);
    }
  }

  function connect() {
    ws = new WebSocket(cfg.wsUrl);

    ws.onopen = () => {
      setStatus("Conectado. Autenticando...");
      send("auth", { token: sessionToken });
    };

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.event === "auth_ok") {
        setStatus(`Autenticado: ${msg.payload.username}`);
        send("room_list", {});
      }

      if (msg.event === "room_created") {
        localStorage.setItem("dk_room_id", msg.payload.room_id);
      }

      if (msg.event === "room_joined") {
        localStorage.setItem("dk_room_id", msg.payload.room_id);
        if (msg.payload.players < 2) {
          setStatus("Aguardando segundo jogador...");
        } else {
          setStatus("Partida iniciando...");
        }
      }

      if (msg.event === "room_list_result") {
        renderRooms(msg.payload.rooms || []);
      }

      if (msg.event === "match_start") {
        localStorage.setItem("dk_match_id", msg.payload.match_id);
        navigate("index.php?page=game");
      }

      if (msg.event === "error") {
        const message = msg.payload && msg.payload.message ? `: ${msg.payload.message}` : "";
        setStatus(`Erro: ${msg.payload.code}${message}`);
      }
    };

    ws.onclose = () => {
      if (!allowReconnect) {
        return;
      }
      setStatus("Conexao fechada. Reconectando...");
      setTimeout(async () => {
        if (!allowReconnect) {
          return;
        }
        try {
          await refreshSessionToken();
          connect();
        } catch {
          setStatus("Erro: sessao invalida");
        }
      }, 1000);
    };
  }

  async function refreshSessionToken() {
    const res = await fetch("web/api/session.php", { credentials: "same-origin", cache: "no-store" });
    if (!res.ok) {
      throw new Error("session fetch failed");
    }
    const data = await res.json();
    if (!data || !data.ok || !data.token) {
      throw new Error("session token missing");
    }
    sessionToken = data.token;
  }

  document.getElementById("createRoomBtn").addEventListener("click", () => {
    const roomName = roomNameInput.value.trim() || "Sala 1";
    send("room_create", { room_name: roomName });
  });

  document.getElementById("refreshBtn").addEventListener("click", () => {
    send("room_list", {});
  });

  roomsBody.addEventListener("click", (ev) => {
    const target = ev.target;
    if (!(target instanceof HTMLButtonElement)) {
      return;
    }
    const roomId = target.dataset.roomId;
    if (!roomId) {
      return;
    }
    send("room_join", { room_id: roomId });
  });

  window.addEventListener("beforeunload", () => {
    allowReconnect = false;
    if (ws) {
      ws.close();
    }
  });

  refreshSessionToken().then(connect).catch(() => setStatus("Erro: sessao invalida"));
})();
