const statusEl = document.getElementById('lobby-status');
const roomListEl = document.getElementById('room-list');
const createRoomForm = document.getElementById('create-room-form');
const roomNameEl = document.getElementById('room-name');
const leaveRoomBtn = document.getElementById('leave-room-btn');

let ws;
let requestId = 0;
let currentRoomId = localStorage.getItem('dk_room_id') || null;
let currentMatchId = localStorage.getItem('dk_match_id') || null;

async function fetchSession() {
  const endpoint = `${window.DK_SESSION.sessionEndpoint}?_=${Date.now()}`;
  const response = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' });
  const data = await response.json();
  if (!data.ok) {
    window.location.href = '/index.php?page=login';
    return null;
  }
  return data;
}

function send(event, payload = {}) {
  ws.send(JSON.stringify({ event, payload, request_id: String(++requestId) }));
}

function setRoomState(roomId) {
  currentRoomId = roomId;
  if (roomId) {
    localStorage.setItem('dk_room_id', roomId);
    leaveRoomBtn.style.display = 'inline-flex';
    return;
  }
  localStorage.removeItem('dk_room_id');
  localStorage.removeItem('dk_match_id');
  currentMatchId = null;
  leaveRoomBtn.style.display = 'none';
}

function renderRooms(rooms) {
  roomListEl.innerHTML = '';
  if (!rooms.length) {
    roomListEl.innerHTML = '<div class="muted">Nenhuma sala aberta</div>';
    return;
  }

  rooms.forEach((room) => {
    const card = document.createElement('div');
    card.className = 'room-card';
    card.innerHTML = `
      <div>
        <strong>${room.name}</strong>
        <div class="muted">${room.players}/2 jogadores</div>
      </div>
      <button type="button">Entrar</button>
    `;
    card.querySelector('button').addEventListener('click', () => {
      send('room_join', { room_id: room.room_id });
    });
    roomListEl.appendChild(card);
  });
}

async function connect() {
  const session = await fetchSession();
  if (!session) return;
  setRoomState(currentRoomId);

  ws = new WebSocket(session.ws_url);
  ws.addEventListener('open', () => {
    statusEl.textContent = 'Autenticando...';
    send('auth', { token: session.token });
  });

  ws.addEventListener('message', (message) => {
    const data = JSON.parse(message.data);
    const { event, payload } = data;

    if (event === 'auth_ok') {
      statusEl.textContent = `Conectado como ${payload.username}`;
      if (currentRoomId && currentMatchId) {
        send('room_join', { room_id: currentRoomId });
      }
      return;
    }

    if (event === 'room_list_result') {
      renderRooms(payload.rooms);
      return;
    }

    if (event === 'room_created' || event === 'room_joined') {
      setRoomState(payload.room_id);
      statusEl.textContent = 'Sala pronta';
      send('room_list');
      return;
    }

    if (event === 'room_left') {
      if (payload.room_id === currentRoomId) {
        setRoomState(null);
      }
      statusEl.textContent = 'Saiu da sala';
      send('room_list');
      return;
    }

    if (event === 'room_closed') {
      if (payload.room_id === currentRoomId) {
        setRoomState(null);
        statusEl.textContent = 'Sala encerrada';
      }
      send('room_list');
      return;
    }

    if (event === 'match_start') {
      localStorage.setItem('dk_match_id', payload.match_id);
      currentMatchId = payload.match_id;
      window.location.href = '/index.php?page=game';
      return;
    }

    if (event === 'error') {
      if (payload.code === 'ROOM_NOT_FOUND') {
        setRoomState(null);
      }
      statusEl.textContent = `${payload.code}: ${payload.message}`;
    }
  });

  ws.addEventListener('close', () => {
    statusEl.textContent = 'Conexão encerrada';
  });
}

createRoomForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const roomName = roomNameEl.value.trim();
  if (!roomName) return;
  send('room_create', { room_name: roomName });
  roomNameEl.value = '';
});

leaveRoomBtn.addEventListener('click', () => {
  if (!currentRoomId) return;
  send('room_leave');
});

connect();
