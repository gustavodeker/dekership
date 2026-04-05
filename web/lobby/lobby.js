const statusEl = document.getElementById('lobby-status');
const roomListEl = document.getElementById('room-list');
const createRoomForm = document.getElementById('create-room-form');
const roomNameEl = document.getElementById('room-name');

let ws;
let requestId = 0;

async function fetchSession() {
  const response = await fetch(window.DK_SESSION.sessionEndpoint, { credentials: 'same-origin' });
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
      return;
    }

    if (event === 'room_list_result') {
      renderRooms(payload.rooms);
      return;
    }

    if (event === 'room_created' || event === 'room_joined') {
      localStorage.setItem('dk_room_id', payload.room_id);
      statusEl.textContent = 'Sala pronta';
      send('room_list');
      return;
    }

    if (event === 'match_start') {
      localStorage.setItem('dk_match_id', payload.match_id);
      window.location.href = '/index.php?page=game';
      return;
    }

    if (event === 'error') {
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

connect();
