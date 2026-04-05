const canvas = document.getElementById('game-canvas');
const context = canvas.getContext('2d');
const statusNode = document.getElementById('game-status');
const scoreSelf = document.getElementById('score-self');
const scoreOpponent = document.getElementById('score-opponent');

let ws;
let requestId = 0;
let inputSeq = 0;
let myUserId = null;
let state = null;
const pressed = { left: false, right: false };

async function fetchSession() {
  const response = await fetch(window.DK_SESSION.sessionEndpoint, { credentials: 'same-origin' });
  const data = await response.json();
  if (!data.ok) {
    window.location.href = '/index.php?page=login';
    return null;
  }
  myUserId = data.user_id;
  return data;
}

function send(event, payload = {}) {
  ws.send(JSON.stringify({ event, payload, request_id: String(++requestId) }));
}

function currentMoveX() {
  if (pressed.left && !pressed.right) return -1;
  if (pressed.right && !pressed.left) return 1;
  return 0;
}

function sendInput(shoot = false) {
  send('player_input', {
    seq: ++inputSeq,
    move_x: currentMoveX(),
    shoot,
  });
}

function drawPlayer(player, y, color) {
  context.fillStyle = color;
  context.fillRect(player.x * 8, y, 60, 16);
}

function drawProjectile(projectile) {
  context.fillStyle = '#f59e0b';
  context.fillRect(projectile.x * 8 + 28, projectile.y * 5, 4, 12);
}

function render() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#17324f';
  context.fillRect(0, 0, canvas.width, canvas.height);

  if (state) {
    drawPlayer(state.p1, 470, state.p1.user_id === myUserId ? '#22c55e' : '#3b82f6');
    drawPlayer(state.p2, 50, state.p2.user_id === myUserId ? '#22c55e' : '#ef4444');
    state.projectiles.forEach(drawProjectile);
    const selfIsBottom = state.p1.user_id === myUserId;
    scoreSelf.textContent = selfIsBottom ? state.score.p1 : state.score.p2;
    scoreOpponent.textContent = selfIsBottom ? state.score.p2 : state.score.p1;
  }

  requestAnimationFrame(render);
}

async function connect() {
  const session = await fetchSession();
  if (!session) return;

  ws = new WebSocket(session.ws_url);
  ws.addEventListener('open', () => send('auth', { token: session.token }));

  ws.addEventListener('message', (message) => {
    const data = JSON.parse(message.data);
    const { event, payload } = data;

    if (event === 'auth_ok') {
      statusNode.textContent = 'Conectado';
      return;
    }

    if (event === 'match_start') {
      localStorage.setItem('dk_match_id', payload.match_id);
      statusNode.textContent = 'Partida iniciada';
      return;
    }

    if (event === 'state') {
      state = payload;
      return;
    }

    if (event === 'match_end') {
      const won = Number(payload.winner_user_id) === Number(myUserId);
      statusNode.textContent = won ? 'Vitória' : 'Derrota';
      localStorage.removeItem('dk_room_id');
      localStorage.removeItem('dk_match_id');
      setTimeout(() => {
        window.location.href = '/index.php?page=lobby';
      }, 2000);
      return;
    }

    if (event === 'error') {
      statusNode.textContent = `${payload.code}: ${payload.message}`;
    }
  });
}

window.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') pressed.left = true;
  if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') pressed.right = true;
  if (event.code === 'Space') sendInput(true);
  else sendInput(false);
});

window.addEventListener('keyup', (event) => {
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') pressed.left = false;
  if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') pressed.right = false;
  sendInput(false);
});

connect();
render();
