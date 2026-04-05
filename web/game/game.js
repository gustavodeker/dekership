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
const pressed = { left: false, right: false, up: false, down: false };
const pointer = { x: 50, y: 50 };
let lastSentAt = 0;
let pendingShot = false;
let flushTimer = null;

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

function currentMoveY() {
  if (pressed.up && !pressed.down) return -1;
  if (pressed.down && !pressed.up) return 1;
  return 0;
}

function sendInput(shoot = false) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  send('player_input', {
    seq: ++inputSeq,
    move_x: currentMoveX(),
    move_y: currentMoveY(),
    aim_x: pointer.x,
    aim_y: pointer.y,
    shoot,
  });
}

function arenaToCanvasX(x) {
  return (x / 100) * canvas.width;
}

function arenaToCanvasY(y) {
  return (y / 100) * canvas.height;
}

function syncPointerFromEvent(event) {
  const rect = canvas.getBoundingClientRect();
  const canvasX = ((event.clientX - rect.left) / rect.width) * canvas.width;
  const canvasY = ((event.clientY - rect.top) / rect.height) * canvas.height;
  pointer.x = Math.max(0, Math.min(100, (canvasX / canvas.width) * 100));
  pointer.y = Math.max(0, Math.min(100, (canvasY / canvas.height) * 100));
}

function scheduleInput() {
  const now = performance.now();
  const elapsed = now - lastSentAt;
  if (pendingShot || elapsed >= 33) {
    if (flushTimer) {
      clearTimeout(flushTimer);
      flushTimer = null;
    }
    lastSentAt = now;
    sendInput(pendingShot);
    pendingShot = false;
    return;
  }
  if (flushTimer) return;
  flushTimer = window.setTimeout(() => {
    flushTimer = null;
    scheduleInput();
  }, 33 - elapsed);
}

function drawPlayer(player, color) {
  const x = arenaToCanvasX(player.x);
  const y = arenaToCanvasY(player.y);
  const angle = Math.atan2(player.aim_y - player.y, player.aim_x - player.x);

  context.save();
  context.translate(x, y);
  context.rotate(angle);
  context.fillStyle = color;
  context.beginPath();
  context.moveTo(22, 0);
  context.lineTo(-16, -12);
  context.lineTo(-10, 0);
  context.lineTo(-16, 12);
  context.closePath();
  context.fill();
  context.restore();
}

function drawProjectile(projectile) {
  context.fillStyle = '#f59e0b';
  context.beginPath();
  context.arc(arenaToCanvasX(projectile.x), arenaToCanvasY(projectile.y), 4, 0, Math.PI * 2);
  context.fill();
}

function drawObstacle(obstacle) {
  context.fillStyle = '#334155';
  context.fillRect(
    arenaToCanvasX(obstacle.x),
    arenaToCanvasY(obstacle.y),
    arenaToCanvasX(obstacle.width),
    arenaToCanvasY(obstacle.height)
  );
  context.strokeStyle = '#64748b';
  context.lineWidth = 2;
  context.strokeRect(
    arenaToCanvasX(obstacle.x),
    arenaToCanvasY(obstacle.y),
    arenaToCanvasX(obstacle.width),
    arenaToCanvasY(obstacle.height)
  );
}

function render() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#17324f';
  context.fillRect(0, 0, canvas.width, canvas.height);

  if (state) {
    (state.obstacles || []).forEach(drawObstacle);
    drawPlayer(state.p1, state.p1.user_id === myUserId ? '#22c55e' : '#3b82f6');
    drawPlayer(state.p2, state.p2.user_id === myUserId ? '#22c55e' : '#ef4444');
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
  if (event.key === 'ArrowUp' || event.key.toLowerCase() === 'w') pressed.up = true;
  if (event.key === 'ArrowDown' || event.key.toLowerCase() === 's') pressed.down = true;
  scheduleInput();
});

window.addEventListener('keyup', (event) => {
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') pressed.left = false;
  if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') pressed.right = false;
  if (event.key === 'ArrowUp' || event.key.toLowerCase() === 'w') pressed.up = false;
  if (event.key === 'ArrowDown' || event.key.toLowerCase() === 's') pressed.down = false;
  scheduleInput();
});

canvas.addEventListener('mousemove', (event) => {
  syncPointerFromEvent(event);
  scheduleInput();
});

canvas.addEventListener('mousedown', (event) => {
  if (event.button !== 0) return;
  syncPointerFromEvent(event);
  pendingShot = true;
  scheduleInput();
});

connect();
render();
