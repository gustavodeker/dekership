(function () {
  const cfg = window.DEKERSHIP_GAME_CFG;
  const statusText = document.getElementById("statusText");
  const myScoreEl = document.getElementById("myScore");
  const enemyScoreEl = document.getElementById("enemyScore");
  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");

  let ws;
  let myUserId = null;
  let sessionToken = cfg.token;
  let seq = 0;
  let moveX = 0;
  let shootPressed = false;
  let side = "bottom";
  let state = null;
  let matchStarted = false;
  let allowReconnect = true;

  function setStatus(text) {
    statusText.textContent = text;
  }

  function send(event, payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ event, payload: payload || {} }));
    }
  }

  function navigate(url) {
    allowReconnect = false;
    if (ws) {
      ws.close();
    }
    window.location.href = url;
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
        myUserId = msg.payload.user_id;
        setStatus("Autenticado. Entrando na sala...");
        if (cfg.roomId) {
          send("room_join", { room_id: cfg.roomId });
        } else {
          setStatus("Sala nao definida. Volte ao lobby.");
        }
      }

      if (msg.event === "room_joined") {
        side = msg.payload.side;
        cfg.roomId = msg.payload.room_id;
        localStorage.setItem("dk_room_id", cfg.roomId);
        setStatus(msg.payload.players < 2 ? "Aguardando segundo jogador..." : "Aguardando inicio da partida...");
      }

      if (msg.event === "match_start") {
        cfg.matchId = msg.payload.match_id;
        localStorage.setItem("dk_match_id", cfg.matchId);
        matchStarted = true;
        setStatus("Partida em andamento");
      }

      if (msg.event === "state") {
        state = msg.payload;
        const p1 = Number(state.score && state.score.p1 ? state.score.p1 : 0);
        const p2 = Number(state.score && state.score.p2 ? state.score.p2 : 0);
        if (side === "bottom") {
          myScoreEl.textContent = String(p1);
          enemyScoreEl.textContent = String(p2);
        } else {
          myScoreEl.textContent = String(p2);
          enemyScoreEl.textContent = String(p1);
        }
      }

      if (msg.event === "match_end") {
        const winner = msg.payload.winner_user_id;
        matchStarted = false;
        setStatus(winner === myUserId ? "Vitoria" : "Derrota");
        setTimeout(() => {
          navigate("index.php?page=lobby");
        }, 2000);
      }

      if (msg.event === "error") {
        const code = msg.payload && msg.payload.code ? msg.payload.code : "UNKNOWN";
        const message = msg.payload && msg.payload.message ? `: ${msg.payload.message}` : "";
        if (code === "INVALID_STATE" && message.includes("partida nao iniciada") && !matchStarted) {
          return;
        }
        if (code === "INVALID_STATE" && message.includes("sala nao encontrada")) {
          setStatus("Sala invalida. Voltando ao lobby...");
          setTimeout(() => {
            navigate("index.php?page=lobby");
          }, 800);
          return;
        }
        setStatus(`Erro: ${code}${message}`);
      }
    };

    ws.onclose = () => {
      matchStarted = false;
      if (!allowReconnect) {
        return;
      }
      setStatus("Conexao encerrada. Reconectando...");
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

  function inputLoop() {
    if (!matchStarted) {
      return;
    }
    seq += 1;
    send("player_input", { seq, move_x: moveX, shoot: shootPressed });
    shootPressed = false;
  }

  function drawLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#0d1628";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!state) {
      requestAnimationFrame(drawLoop);
      return;
    }

    const p1 = state.p1 || { x: 50, y: 90 };
    const p2 = state.p2 || { x: 50, y: 10 };

    const toX = (x) => (x / 100) * canvas.width;
    const toY = (y) => (y / 100) * canvas.height;

    ctx.fillStyle = "#2ea043";
    ctx.fillRect(toX(p1.x) - 20, toY(p1.y) - 8, 40, 16);

    ctx.fillStyle = "#e5534b";
    ctx.fillRect(toX(p2.x) - 20, toY(p2.y) - 8, 40, 16);

    const projectiles = Array.isArray(state.projectiles) ? state.projectiles : [];
    ctx.fillStyle = "#f0c674";
    for (const shot of projectiles) {
      ctx.beginPath();
      ctx.arc(toX(shot.x), toY(shot.y), 4, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(drawLoop);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft" || e.key.toLowerCase() === "a") {
      moveX = -1;
    }
    if (e.key === "ArrowRight" || e.key.toLowerCase() === "d") {
      moveX = 1;
    }
    if (e.code === "Space") {
      shootPressed = true;
    }
  });

  document.addEventListener("keyup", (e) => {
    if (e.key === "ArrowLeft" || e.key.toLowerCase() === "a") {
      if (moveX === -1) {
        moveX = 0;
      }
    }
    if (e.key === "ArrowRight" || e.key.toLowerCase() === "d") {
      if (moveX === 1) {
        moveX = 0;
      }
    }
  });

  document.getElementById("leaveBtn").addEventListener("click", () => {
    navigate("index.php?page=lobby");
  });

  window.addEventListener("beforeunload", () => {
    allowReconnect = false;
    if (ws) {
      ws.close();
    }
  });

  setInterval(() => send("ping", { ts: Date.now() }), 5000);
  setInterval(inputLoop, 50);
  drawLoop();
  refreshSessionToken().then(connect).catch(() => setStatus("Erro: sessao invalida"));
})();
