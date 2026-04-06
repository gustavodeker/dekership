const canvas = document.getElementById('game-canvas');
const context = canvas.getContext('2d');
const statusNode = document.getElementById('game-status');
const scoreSelf = document.getElementById('score-self');
const scoreOpponent = document.getElementById('score-opponent');
const startOverlayNode = document.getElementById('game-start-overlay');
const DESIGN_WIDTH = canvas.width;
const DESIGN_HEIGHT = canvas.height;

let ws;
let requestId = 0;
let inputSeq = 0;
let myUserId = null;
let state = null;
let renderState = null;
let renderSmoothing = 0.25;
const pressed = { left: false, right: false, up: false, down: false };
const pointer = { x: 50, y: 50 };
let lastSentAt = 0;
let pendingShot = false;
let flushTimer = null;
let resizeHandle = null;
let matchStarted = false;
let startCountdownInterval = null;
let startOverlayTimeout = null;
let endCountdownInterval = null;
let controlsLocked = false;
let playerHitRadius = 5.4;
let projectileHitRadius = 0.6;
let hitFeedbackUntil = 0;
let hitFeedbackColor = '#22c55e';

function applyCanvasScale() {
  const panel = canvas.closest('.game-panel');
  if (!panel) return;

  const panelStyle = window.getComputedStyle(panel);
  const paddingLeft = parseFloat(panelStyle.paddingLeft) || 0;
  const paddingRight = parseFloat(panelStyle.paddingRight) || 0;
  const paddingBottom = parseFloat(panelStyle.paddingBottom) || 0;
  const canvasRect = canvas.getBoundingClientRect();
  const panelRect = panel.getBoundingClientRect();

  const availableWidth = Math.max(1, panel.clientWidth - paddingLeft - paddingRight);
  const availableHeight = Math.max(1, panelRect.bottom - canvasRect.top - paddingBottom);
  const scale = Math.min(availableWidth / DESIGN_WIDTH, availableHeight / DESIGN_HEIGHT);

  canvas.style.width = `${Math.floor(DESIGN_WIDTH * scale)}px`;
  canvas.style.height = `${Math.floor(DESIGN_HEIGHT * scale)}px`;
}

function scheduleCanvasScale() {
  if (resizeHandle !== null) {
    cancelAnimationFrame(resizeHandle);
  }
  resizeHandle = requestAnimationFrame(() => {
    resizeHandle = null;
    applyCanvasScale();
  });
}

function clearStartOverlayTimers() {
  if (startCountdownInterval !== null) {
    clearInterval(startCountdownInterval);
    startCountdownInterval = null;
  }
  if (startOverlayTimeout !== null) {
    clearTimeout(startOverlayTimeout);
    startOverlayTimeout = null;
  }
  if (endCountdownInterval !== null) {
    clearInterval(endCountdownInterval);
    endCountdownInterval = null;
  }
}

function hideStartOverlay() {
  if (!startOverlayNode) return;
  startOverlayNode.hidden = true;
  startOverlayNode.classList.remove('game-start-overlay--end');
  startOverlayNode.textContent = '';
}

function startMatchCountdown() {
  if (!startOverlayNode) return;
  clearStartOverlayTimers();
  controlsLocked = true;
  pendingShot = false;
  startOverlayNode.classList.remove('game-start-overlay--end');

  let count = 3;
  startOverlayNode.hidden = false;
  startOverlayNode.textContent = String(count);

  startCountdownInterval = window.setInterval(() => {
    count -= 1;
    if (count > 0) {
      startOverlayNode.textContent = String(count);
      return;
    }

    clearStartOverlayTimers();
    startOverlayNode.textContent = 'GO!';
    startOverlayTimeout = window.setTimeout(() => {
      hideStartOverlay();
      controlsLocked = false;
      startOverlayTimeout = null;
    }, 1000);
  }, 1000);
}

function renderMatchEndOverlay(won, count) {
  if (!startOverlayNode) return;
  startOverlayNode.classList.add('game-start-overlay--end');
  startOverlayNode.innerHTML = `
    <div class="game-start-overlay__result">${won ? 'Vit\u00f3ria!' : 'Derrota!'}</div>
    <div class="game-start-overlay__exit">Saindo em <span class="game-start-overlay__count">${count}</span>...</div>
  `;
}

function startMatchEndCountdown(won) {
  if (!startOverlayNode) return;
  clearStartOverlayTimers();
  controlsLocked = true;
  pendingShot = false;
  startOverlayNode.hidden = false;

  let count = 3;
  renderMatchEndOverlay(won, count);
  endCountdownInterval = window.setInterval(() => {
    count -= 1;
    if (count >= 1) {
      renderMatchEndOverlay(won, count);
      return;
    }
    clearStartOverlayTimers();
    localStorage.removeItem('dk_room_id');
    localStorage.removeItem('dk_match_id');
    window.location.href = '/index.php?page=lobby';
  }, 1000);
}

function countdownShownStorageKey(matchId) {
  return `dk_match_countdown_shown_${matchId}`;
}

function shouldShowStartCountdown(matchId) {
  if (!matchId) return true;
  const key = countdownShownStorageKey(matchId);
  const alreadyShown = localStorage.getItem(key) === '1';
  if (alreadyShown) return false;
  localStorage.setItem(key, '1');
  return true;
}

async function fetchSession() {
  const endpoint = `${window.DK_SESSION.sessionEndpoint}?_=${Date.now()}`;
  const response = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' });
  const data = await response.json();
  if (!data.ok) {
    window.location.href = '/index.php?page=login';
    return null;
  }
  myUserId = data.user_id;
  if (typeof data.render_smoothing === 'number') {
    renderSmoothing = Math.max(0, Math.min(1, data.render_smoothing));
  }
  if (typeof data.player_hitbox_radius === 'number') {
    playerHitRadius = Math.max(0.1, data.player_hitbox_radius);
  }
  if (typeof data.projectile_hitbox_radius === 'number') {
    projectileHitRadius = Math.max(0.1, data.projectile_hitbox_radius);
  }
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
  if (controlsLocked) return;
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

function lerp(from, to, alpha) {
  return from + (to - from) * alpha;
}

function arenaRadiusToCanvasRadius(radius) {
  return Math.min(arenaToCanvasX(radius), arenaToCanvasY(radius));
}

function cloneGameState(snapshot) {
  return {
    ...snapshot,
    p1: { ...snapshot.p1 },
    p2: { ...snapshot.p2 },
    score: { ...snapshot.score },
    obstacles: (snapshot.obstacles || []).map((obstacle) => ({ ...obstacle })),
    projectiles: (snapshot.projectiles || []).map((projectile) => ({ ...projectile })),
  };
}

function blendPlayer(currentPlayer, targetPlayer, alpha) {
  return {
    ...targetPlayer,
    x: lerp(currentPlayer.x, targetPlayer.x, alpha),
    y: lerp(currentPlayer.y, targetPlayer.y, alpha),
    aim_x: lerp(currentPlayer.aim_x, targetPlayer.aim_x, alpha),
    aim_y: lerp(currentPlayer.aim_y, targetPlayer.aim_y, alpha),
  };
}

function blendProjectiles(currentProjectiles, targetProjectiles, alpha) {
  const currentById = new Map(
    currentProjectiles
      .filter((projectile) => Number.isFinite(projectile.projectile_id))
      .map((projectile) => [projectile.projectile_id, projectile])
  );

  return targetProjectiles.map((targetProjectile) => {
    const projectileId = targetProjectile.projectile_id;
    const currentProjectile = Number.isFinite(projectileId) ? currentById.get(projectileId) : null;
    if (!currentProjectile) {
      return { ...targetProjectile };
    }
    return {
      ...targetProjectile,
      x: lerp(currentProjectile.x, targetProjectile.x, alpha),
      y: lerp(currentProjectile.y, targetProjectile.y, alpha),
    };
  });
}

function blendState(current, target, alpha) {
  if (!current) {
    return cloneGameState(target);
  }
  return {
    ...target,
    p1: blendPlayer(current.p1, target.p1, alpha),
    p2: blendPlayer(current.p2, target.p2, alpha),
    score: { ...target.score },
    obstacles: (target.obstacles || []).map((obstacle) => ({ ...obstacle })),
    projectiles: blendProjectiles(current.projectiles || [], target.projectiles || [], alpha),
  };
}

function syncPointerFromEvent(event) {
  const rect = canvas.getBoundingClientRect();
  const canvasX = ((event.clientX - rect.left) / rect.width) * canvas.width;
  const canvasY = ((event.clientY - rect.top) / rect.height) * canvas.height;
  pointer.x = Math.max(0, Math.min(100, (canvasX / canvas.width) * 100));
  pointer.y = Math.max(0, Math.min(100, (canvasY / canvas.height) * 100));
}

function scheduleInput() {
  if (controlsLocked) return;
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

  context.save();
  context.strokeStyle = 'rgba(34, 197, 94, 0.7)';
  context.lineWidth = 2;
  context.beginPath();
  context.arc(x, y, arenaRadiusToCanvasRadius(playerHitRadius), 0, Math.PI * 2);
  context.stroke();
  context.restore();

  if (player.username) {
    context.save();
    context.font = '600 14px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'bottom';
    context.lineWidth = 4;
    context.strokeStyle = 'rgba(15, 23, 42, 0.9)';
    context.fillStyle = '#f8fafc';
    context.strokeText(player.username, x, y - 18);
    context.fillText(player.username, x, y - 18);
    context.restore();
  }
}

function drawProjectile(projectile) {
  const x = arenaToCanvasX(projectile.x);
  const y = arenaToCanvasY(projectile.y);
  context.fillStyle = '#f59e0b';
  context.beginPath();
  context.arc(x, y, 4, 0, Math.PI * 2);
  context.fill();

  context.save();
  context.strokeStyle = 'rgba(245, 158, 11, 0.9)';
  context.lineWidth = 1.5;
  context.beginPath();
  context.arc(x, y, arenaRadiusToCanvasRadius(projectileHitRadius), 0, Math.PI * 2);
  context.stroke();
  context.restore();
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

function showHitFeedback(color) {
  hitFeedbackColor = color;
  hitFeedbackUntil = performance.now() + 1000;
}

function drawHitFeedback() {
  if (performance.now() > hitFeedbackUntil) return;
  context.save();
  context.font = '700 48px Arial';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.lineWidth = 6;
  context.strokeStyle = 'rgba(15, 23, 42, 0.85)';
  context.fillStyle = hitFeedbackColor;
  context.strokeText('Hit!', canvas.width / 2, canvas.height / 2);
  context.fillText('Hit!', canvas.width / 2, canvas.height / 2);
  context.restore();
}

function render() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#17324f';
  context.fillRect(0, 0, canvas.width, canvas.height);

  if (state) {
    renderState = blendState(renderState, state, renderSmoothing);
    (renderState.obstacles || []).forEach(drawObstacle);
    drawPlayer(renderState.p1, renderState.p1.user_id === myUserId ? '#22c55e' : '#3b82f6');
    drawPlayer(renderState.p2, renderState.p2.user_id === myUserId ? '#22c55e' : '#ef4444');
    renderState.projectiles.forEach(drawProjectile);
    const selfIsBottom = state.p1.user_id === myUserId;
    scoreSelf.textContent = selfIsBottom ? state.score.p1 : state.score.p2;
    scoreOpponent.textContent = selfIsBottom ? state.score.p2 : state.score.p1;
  }
  drawHitFeedback();

  requestAnimationFrame(render);
}

function updateStatusFromState(payload) {
  if (!matchStarted) return;
  if (payload.paused) {
    statusNode.textContent = `Partida pausada: aguardando reconexao (${payload.pause_remaining_seconds}s)`;
    return;
  }
  statusNode.textContent = 'Partida em andamento';
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
      const matchId = payload.match_id;
      localStorage.setItem('dk_match_id', matchId);
      matchStarted = true;
      statusNode.textContent = 'Partida iniciando...';
      if (shouldShowStartCountdown(matchId)) {
        startMatchCountdown();
      } else {
        controlsLocked = false;
        hideStartOverlay();
      }
      return;
    }

    if (event === 'state') {
      state = payload;
      if (!renderState) {
        renderState = cloneGameState(payload);
      }
      updateStatusFromState(payload);
      return;
    }

    if (event === 'hit') {
      if (Number(payload.attacker) === Number(myUserId)) {
        showHitFeedback('#22c55e');
      } else if (Number(payload.target) === Number(myUserId)) {
        showHitFeedback('#ef4444');
      }
      return;
    }

    if (event === 'match_end') {
      clearStartOverlayTimers();
      hideStartOverlay();
      const won = Number(payload.winner_user_id) === Number(myUserId);
      statusNode.textContent = won ? 'Vit\u00f3ria' : 'Derrota';
      startMatchEndCountdown(won);
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

window.addEventListener('resize', scheduleCanvasScale);
window.addEventListener('orientationchange', scheduleCanvasScale);
scheduleCanvasScale();

connect();
render();
