const canvas = document.getElementById('open-world-canvas');
const context = canvas.getContext('2d');
const statusNode = document.getElementById('open-world-status');
const statsNode = document.getElementById('open-world-stats');
const deathOverlayNode = document.getElementById('open-world-death-overlay');
const deathCountdownNode = document.getElementById('open-world-death-countdown');
const respawnButton = document.getElementById('open-world-respawn-btn');
const mineCooldownValueNode = document.getElementById('mine-cooldown-value');
const shieldRegenValueNode = document.getElementById('shield-regen-value');
const DESIGN_WIDTH = canvas.width;
const DESIGN_HEIGHT = canvas.height;

let ws;
let requestId = 0;
let inputSeq = 0;
let myUserId = null;
let worldState = null;
let controlsLocked = false;
let matchTickRate = 20;
let mineCooldownTicks = 100;
let hitsToDie = 3;
let mineHitsToDestroy = 2;
let shieldPoints = 2;
let shieldRegenSeconds = 10;
let playerHitRadius = 5.4;
let projectileHitRadius = 0.6;
let mineHitRadius = 2.4;
let showHitbox = true;
let lastSentAt = 0;
let flushTimer = null;
let resizeHandle = null;
const pressed = { left: false, right: false, up: false, down: false };
const pointer = { x: 50, y: 50 };
let pendingShot = false;
let pendingMine = false;
const floatingTexts = [];
const knownMinePositions = new Map();

const playerFlashEffects = new Map();
const playerKnockbackEffects = new Map();
const mineFlashEffects = new Map();
const shieldRegenPulseEffects = new Map();

const shipSprite = new Image();
let shipSpriteReady = false;
const shieldSprite = new Image();
let shieldSpriteReady = false;
const SHIP_RENDER_WIDTH = 156;
const SHIP_RENDER_HEIGHT = 156;
const SHIP_SPRITE_FRAME_SIZE = 512;
const SHIP_SPRITE_GRID_COLS = 9;
const SHIP_SPRITE_GRID_ROWS = 9;
const SHIP_SPRITE_FRAME_COUNT = SHIP_SPRITE_GRID_COLS * SHIP_SPRITE_GRID_ROWS;
const SHIP_SPRITE_ANGLE_OFFSET = 0;
const SHIP_SPRITE_REVERSE_WINDING = true;
const SHIP_SPRITE_ANGLE_STEP = (Math.PI * 2) / SHIP_SPRITE_FRAME_COUNT;
const SHIELD_RENDER_WIDTH = 207;
const SHIELD_RENDER_HEIGHT = 207;
const SHIELD_ANIMATION_FPS = 20;
const SHIELD_REGEN_PULSE_DURATION_MS = 520;
const shieldAtlas = {
  frameWidth: 512,
  frameHeight: 512,
  frames: [],
};

shipSprite.addEventListener('load', () => {
  shipSpriteReady = true;
});
shipSprite.addEventListener('error', () => {
  shipSpriteReady = false;
});
shieldSprite.addEventListener('load', () => {
  shieldSpriteReady = true;
});
shieldSprite.addEventListener('error', () => {
  shieldSpriteReady = false;
});

shipSprite.src = '/web/assets/spritesheet_9x9_512.png';
shieldSprite.src = '/web/assets/spritesheetshild.png';
loadShieldAtlas();
deathOverlayNode.hidden = true;
respawnButton.hidden = true;

function send(event, payload = {}) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ event, payload, request_id: String(++requestId) }));
}

async function loadShieldAtlas() {
  try {
    const response = await fetch('/web/assets/shild.atlas.txt', { cache: 'no-store' });
    if (!response.ok) return;
    parseShieldAtlas(await response.text());
  } catch (error) {
    // Atlas opcional.
  }
}

function parseShieldAtlas(text) {
  const lines = String(text || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  const framesByIndex = new Map();
  for (const line of lines) {
    const separatorIndex = line.indexOf('=');
    if (separatorIndex <= 0) continue;
    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1).trim();
    if (key === 'frame') {
      const [width, height] = value.split(',').map(Number);
      if (Number.isFinite(width) && width > 0) shieldAtlas.frameWidth = width;
      if (Number.isFinite(height) && height > 0) shieldAtlas.frameHeight = height;
      continue;
    }
    if (!key.startsWith('frame_')) continue;
    const match = key.match(/^frame_(\d+)$/);
    if (!match) continue;
    const [sx, sy, sw, sh] = value.split(',').map(Number);
    if (![sx, sy, sw, sh].every(Number.isFinite)) continue;
    framesByIndex.set(Number(match[1]), { sx, sy, sw, sh });
  }
  const ordered = Array.from(framesByIndex.keys())
    .sort((a, b) => a - b)
    .map((index) => framesByIndex.get(index))
    .filter(Boolean);
  if (ordered.length > 0) {
    shieldAtlas.frames = ordered;
  }
}

function getShieldFrame(now = performance.now()) {
  if (!shieldAtlas.frames.length) return null;
  const frameIndex = Math.floor((now / 1000) * SHIELD_ANIMATION_FPS) % shieldAtlas.frames.length;
  return shieldAtlas.frames[frameIndex];
}

function normalizeAngleRad(angle) {
  const fullTurn = Math.PI * 2;
  let normalized = angle % fullTurn;
  if (normalized < 0) normalized += fullTurn;
  return normalized;
}

function angleToShipFrameIndex(angle) {
  const orientedAngle = SHIP_SPRITE_REVERSE_WINDING ? -angle : angle;
  const normalized = normalizeAngleRad(orientedAngle - SHIP_SPRITE_ANGLE_OFFSET);
  return Math.round(normalized / SHIP_SPRITE_ANGLE_STEP) % SHIP_SPRITE_FRAME_COUNT;
}

function frameIndexToSpritePosition(frameIndex) {
  const clamped = Math.max(0, Math.min(SHIP_SPRITE_FRAME_COUNT - 1, frameIndex));
  const col = clamped % SHIP_SPRITE_GRID_COLS;
  const row = Math.floor(clamped / SHIP_SPRITE_GRID_COLS);
  return { sx: col * SHIP_SPRITE_FRAME_SIZE, sy: row * SHIP_SPRITE_FRAME_SIZE };
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

function sendInput(shoot = false, dropMine = false) {
  if (controlsLocked) return;
  const safeShoot = isSelfInvulnerable() ? false : shoot;
  send('player_input', {
    seq: ++inputSeq,
    move_x: currentMoveX(),
    move_y: currentMoveY(),
    aim_x: pointer.x,
    aim_y: pointer.y,
    shoot: safeShoot,
    drop_mine: dropMine,
  });
}

function scheduleInput() {
  if (controlsLocked) return;
  const now = performance.now();
  const elapsed = now - lastSentAt;
  if (pendingShot || pendingMine || elapsed >= 33) {
    if (flushTimer) {
      clearTimeout(flushTimer);
      flushTimer = null;
    }
    lastSentAt = now;
    sendInput(pendingShot, pendingMine);
    pendingShot = false;
    pendingMine = false;
    return;
  }
  if (flushTimer) return;
  flushTimer = window.setTimeout(() => {
    flushTimer = null;
    scheduleInput();
  }, 33 - elapsed);
}

function syncPointerFromEvent(event) {
  const rect = canvas.getBoundingClientRect();
  const canvasX = ((event.clientX - rect.left) / rect.width) * canvas.width;
  const canvasY = ((event.clientY - rect.top) / rect.height) * canvas.height;
  pointer.x = Math.max(0, Math.min(100, (canvasX / canvas.width) * 100));
  pointer.y = Math.max(0, Math.min(100, (canvasY / canvas.height) * 100));
}

function arenaToCanvasX(x) {
  return (x / 100) * canvas.width;
}

function arenaToCanvasY(y) {
  return (y / 100) * canvas.height;
}

function arenaRadiusToCanvasRadius(radius) {
  return Math.min(arenaToCanvasX(radius), arenaToCanvasY(radius));
}

function getSelfPlayer() {
  if (!worldState || !Array.isArray(worldState.players)) return null;
  return worldState.players.find((player) => Number(player.user_id) === Number(myUserId)) || null;
}

function isSelfInvulnerable() {
  const selfPlayer = getSelfPlayer();
  if (!selfPlayer) return false;
  const tick = Number(worldState?.tick || 0);
  return Number(selfPlayer.invulnerable_until_tick || 0) > tick;
}

function findPlayerByUserId(snapshot, userId) {
  if (!snapshot || !Array.isArray(snapshot.players)) return null;
  return snapshot.players.find((player) => Number(player.user_id) === Number(userId)) || null;
}

function updateDeathOverlay() {
  const selfPlayer = getSelfPlayer();
  if (!selfPlayer || selfPlayer.alive) {
    controlsLocked = false;
    deathOverlayNode.hidden = true;
    respawnButton.hidden = true;
    return;
  }
  controlsLocked = true;
  deathOverlayNode.hidden = false;
  const remainingTicks = Math.max(0, Number(selfPlayer.dead_until_tick || 0) - Number(worldState.tick || 0));
  const remainingSeconds = Math.ceil(remainingTicks / Math.max(1, matchTickRate));
  if (remainingSeconds > 0) {
    deathCountdownNode.textContent = `Renascer em ${remainingSeconds}s`;
    respawnButton.hidden = true;
  } else {
    deathCountdownNode.textContent = 'Pronto para renascer';
    respawnButton.hidden = false;
  }
}

function mineCooldownRemainingSeconds(selfPlayer) {
  if (!selfPlayer) return 0;
  const lastMineTick = Number(selfPlayer.last_mine_tick ?? -1000000);
  const elapsedTicks = Number(worldState.tick ?? 0) - lastMineTick;
  const remainingTicks = Math.max(0, mineCooldownTicks - elapsedTicks);
  return remainingTicks / Math.max(1, matchTickRate);
}

function shieldRegenRemainingSeconds(selfPlayer) {
  if (!selfPlayer || shieldPoints <= 0) return 0;
  const currentShield = Math.max(0, Math.floor(Number(selfPlayer.shield_points ?? 0)));
  if (currentShield >= shieldPoints) return 0;
  const tick = Number(worldState.tick ?? 0);
  const lastDamageTick = Math.max(0, Math.floor(Number(selfPlayer.last_damage_tick ?? tick)));
  const lastRegenTick = Math.max(lastDamageTick, Math.floor(Number(selfPlayer.last_shield_regen_tick ?? lastDamageTick)));
  const baseTick = Math.max(lastDamageTick, lastRegenTick);
  const regenTicks = Math.max(1, Math.floor(shieldRegenSeconds * Math.max(1, matchTickRate)));
  const elapsedTicks = Math.max(0, tick - baseTick);
  const remainingTicks = Math.max(0, regenTicks - elapsedTicks);
  return remainingTicks / Math.max(1, matchTickRate);
}

function updateHud() {
  if (!worldState) return;
  const players = Array.isArray(worldState.players) ? worldState.players : [];
  const selfPlayer = getSelfPlayer();
  const alivePlayers = players.filter((player) => Boolean(player.alive)).length;
  const maxPlayers = Number(worldState.max_players || 50);
  const kills = selfPlayer ? Number(selfPlayer.kills || 0) : 0;
  const deaths = selfPlayer ? Number(selfPlayer.deaths || 0) : 0;
  statsNode.textContent = `Players: ${alivePlayers}/${maxPlayers} | K: ${kills} | D: ${deaths}`;
  const mineRemaining = mineCooldownRemainingSeconds(selfPlayer);
  mineCooldownValueNode.textContent = mineRemaining <= 0 ? 'READY' : `${mineRemaining.toFixed(1)}s`;
  const shieldRemaining = shieldRegenRemainingSeconds(selfPlayer);
  shieldRegenValueNode.textContent = shieldRemaining <= 0 ? 'READY' : `${shieldRemaining.toFixed(1)}s`;
}

function drawRectHealthBar(centerX, topY, width, height, ratio, fillColor) {
  const clamped = Math.max(0, Math.min(1, ratio));
  const left = centerX - (width / 2);
  context.save();
  context.fillStyle = 'rgba(15, 23, 42, 0.9)';
  context.fillRect(left, topY, width, height);
  context.fillStyle = fillColor;
  context.fillRect(left, topY, width * clamped, height);
  context.strokeStyle = 'rgba(248, 250, 252, 0.8)';
  context.lineWidth = 1;
  context.strokeRect(left, topY, width, height);
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

function setMineFlash(mineId, color, durationMs = 110) {
  if (!Number.isFinite(Number(mineId))) return;
  mineFlashEffects.set(Number(mineId), { color, until: performance.now() + durationMs });
}

function getMineFlash(mineId) {
  const effect = mineFlashEffects.get(Number(mineId));
  if (!effect) return null;
  if (performance.now() > effect.until) {
    mineFlashEffects.delete(Number(mineId));
    return null;
  }
  return effect;
}

function setShieldRegenPulse(userId, durationMs = SHIELD_REGEN_PULSE_DURATION_MS) {
  const startAt = performance.now();
  shieldRegenPulseEffects.set(Number(userId), { startAt, endAt: startAt + Math.max(1, durationMs) });
}

function getShieldRegenPulse(userId) {
  const effect = shieldRegenPulseEffects.get(Number(userId));
  if (!effect) return null;
  const now = performance.now();
  const totalDuration = Math.max(1, effect.endAt - effect.startAt);
  const elapsed = now - effect.startAt;
  if (elapsed >= totalDuration) {
    shieldRegenPulseEffects.delete(Number(userId));
    return null;
  }
  return { progress: Math.max(0, Math.min(1, elapsed / totalDuration)) };
}

function setPlayerFlash(userId, color, durationMs = 110, kind = 'hit') {
  if (!Number.isFinite(Number(userId))) return;
  const startAt = performance.now();
  playerFlashEffects.set(Number(userId), {
    color,
    kind,
    startAt,
    durationMs: Math.max(1, durationMs),
    until: startAt + Math.max(1, durationMs),
  });
}

function getPlayerFlash(userId) {
  const effect = playerFlashEffects.get(Number(userId));
  if (!effect) return null;
  if (performance.now() > effect.until) {
    playerFlashEffects.delete(Number(userId));
    return null;
  }
  return {
    ...effect,
    progress: Math.max(0, Math.min(1, (performance.now() - effect.startAt) / Math.max(1, effect.durationMs))),
  };
}

function applyPlayerKnockback(attackerId, targetId, strengthPx = 16, durationMs = 140) {
  const attacker = findPlayerByUserId(worldState, attackerId);
  const target = findPlayerByUserId(worldState, targetId);
  if (!attacker || !target) return;
  const deltaX = target.x - attacker.x;
  const deltaY = target.y - attacker.y;
  const distance = Math.hypot(deltaX, deltaY) || 1;
  playerKnockbackEffects.set(Number(targetId), {
    offsetX: (deltaX / distance) * strengthPx,
    offsetY: (deltaY / distance) * strengthPx,
    startedAt: performance.now(),
    durationMs,
  });
}

function getPlayerKnockbackOffset(userId) {
  const effect = playerKnockbackEffects.get(Number(userId));
  if (!effect) return { x: 0, y: 0 };
  const elapsed = performance.now() - effect.startedAt;
  if (elapsed >= effect.durationMs) {
    playerKnockbackEffects.delete(Number(userId));
    return { x: 0, y: 0 };
  }
  const intensity = 1 - (elapsed / effect.durationMs);
  return { x: effect.offsetX * intensity, y: effect.offsetY * intensity };
}

function drawShieldHoneycombFlash(flash) {
  const pulse = 1 - (flash.progress || 0);
  const radius = Math.min(SHIP_RENDER_WIDTH, SHIP_RENDER_HEIGHT) * 0.34;
  const hexSize = 5.5;
  const rowStep = hexSize * 1.5;
  const colStep = Math.sqrt(3) * hexSize;
  const maxRow = Math.ceil(radius / rowStep) + 1;
  const maxCol = Math.ceil(radius / colStep) + 1;
  context.globalAlpha = 0.85 * pulse;
  context.strokeStyle = '#bfe4ff';
  context.lineWidth = 1.5;
  for (let row = -maxRow; row <= maxRow; row += 1) {
    const y = row * rowStep;
    const xOffset = (Math.abs(row) % 2) * (colStep / 2);
    for (let col = -maxCol; col <= maxCol; col += 1) {
      const x = (col * colStep) + xOffset;
      if ((x * x) + (y * y) > radius * radius) continue;
      drawHexPath(x, y, hexSize);
      context.stroke();
    }
  }
}

function drawHexPath(cx, cy, size) {
  context.beginPath();
  for (let side = 0; side < 6; side += 1) {
    const angle = (Math.PI / 3) * side + (Math.PI / 6);
    const x = cx + (Math.cos(angle) * size);
    const y = cy + (Math.sin(angle) * size);
    if (side === 0) context.moveTo(x, y);
    else context.lineTo(x, y);
  }
  context.closePath();
}

function drawMine(mine) {
  const x = arenaToCanvasX(mine.x);
  const y = arenaToCanvasY(mine.y);
  const isOwnMine = Number(mine.owner_user_id) === Number(myUserId);
  const mineFlash = getMineFlash(mine.mine_id);
  const coreRadius = 7;
  const spikeCount = 8;
  const spikeLength = 5;
  const baseColor = isOwnMine ? '#22c55e' : '#ef4444';

  if (mineFlash) {
    context.save();
    context.globalAlpha = 0.55;
    context.fillStyle = mineFlash.color;
    context.beginPath();
    context.arc(x, y, coreRadius + spikeLength + 1, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }

  context.save();
  context.strokeStyle = baseColor;
  context.lineWidth = 2;
  for (let i = 0; i < spikeCount; i += 1) {
    const angle = (Math.PI * 2 * i) / spikeCount;
    const innerX = x + Math.cos(angle) * (coreRadius + 1);
    const innerY = y + Math.sin(angle) * (coreRadius + 1);
    const outerX = x + Math.cos(angle) * (coreRadius + spikeLength);
    const outerY = y + Math.sin(angle) * (coreRadius + spikeLength);
    context.beginPath();
    context.moveTo(innerX, innerY);
    context.lineTo(outerX, outerY);
    context.stroke();
  }
  context.restore();

  context.fillStyle = baseColor;
  context.beginPath();
  context.arc(x, y, coreRadius, 0, Math.PI * 2);
  context.fill();
  context.strokeStyle = '#0f172a';
  context.lineWidth = 2;
  context.beginPath();
  context.arc(x, y, coreRadius, 0, Math.PI * 2);
  context.stroke();

  if (showHitbox) {
    context.save();
    context.strokeStyle = isOwnMine ? 'rgba(34, 197, 94, 0.85)' : 'rgba(239, 68, 68, 0.85)';
    context.lineWidth = 1.5;
    context.beginPath();
    context.arc(x, y, arenaRadiusToCanvasRadius(mineHitRadius), 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }

  const mineLifeRatio = (mineHitsToDestroy - Number(mine.hits_taken || 0)) / Math.max(1, mineHitsToDestroy);
  drawRectHealthBar(x, y + 17, 30, 6, mineLifeRatio, '#22c55e');
}

function drawProjectile(projectile) {
  const x = arenaToCanvasX(projectile.x);
  const y = arenaToCanvasY(projectile.y);
  const ownProjectile = Number(projectile.owner_user_id) === Number(myUserId);
  context.fillStyle = ownProjectile ? '#22c55e' : '#ef4444';
  context.beginPath();
  context.arc(x, y, 4, 0, Math.PI * 2);
  context.fill();
  if (showHitbox) {
    context.save();
    context.strokeStyle = ownProjectile ? 'rgba(34, 197, 94, 0.9)' : 'rgba(239, 68, 68, 0.9)';
    context.lineWidth = 1.5;
    context.beginPath();
    context.arc(x, y, arenaRadiusToCanvasRadius(projectileHitRadius), 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }
}

function drawPlayer(player) {
  if (!player.alive) return;
  const flash = getPlayerFlash(player.user_id);
  const knockback = getPlayerKnockbackOffset(player.user_id);
  const shieldRegenPulse = getShieldRegenPulse(player.user_id);
  const x = arenaToCanvasX(player.x) + knockback.x;
  const y = arenaToCanvasY(player.y) + knockback.y;
  const invulnerable = Number(player.invulnerable_until_tick || 0) > Number(worldState?.tick || 0);
  const angle = Math.atan2(Number(player.aim_y || player.y) - player.y, Number(player.aim_x || player.x) - player.x);
  const frameIndex = angleToShipFrameIndex(angle);
  const { sx, sy } = frameIndexToSpritePosition(frameIndex);

  context.save();
  context.translate(x, y);
  if (shipSpriteReady) {
    context.drawImage(
      shipSprite,
      sx,
      sy,
      SHIP_SPRITE_FRAME_SIZE,
      SHIP_SPRITE_FRAME_SIZE,
      -SHIP_RENDER_WIDTH / 2,
      -SHIP_RENDER_HEIGHT / 2,
      SHIP_RENDER_WIDTH,
      SHIP_RENDER_HEIGHT
    );
    if (flash) {
      context.save();
      context.globalCompositeOperation = 'source-atop';
      if (flash.kind === 'shield') {
        drawShieldHoneycombFlash(flash);
      } else {
        context.globalAlpha = 0.5;
        context.fillStyle = flash.color;
        context.beginPath();
        context.arc(0, 0, Math.min(SHIP_RENDER_WIDTH, SHIP_RENDER_HEIGHT) * 0.3, 0, Math.PI * 2);
        context.fill();
      }
      context.restore();
    }
  } else {
    context.rotate(angle + SHIP_SPRITE_ANGLE_OFFSET);
    context.fillStyle = '#3b82f6';
    context.beginPath();
    context.moveTo(22, 0);
    context.lineTo(-16, -12);
    context.lineTo(-10, 0);
    context.lineTo(-16, 12);
    context.closePath();
    context.fill();
  }

  if (shieldSpriteReady && Number(player.shield_points ?? 0) > 0) {
    const shieldFrame = getShieldFrame();
    if (shieldFrame) {
      context.drawImage(
        shieldSprite,
        shieldFrame.sx,
        shieldFrame.sy,
        shieldFrame.sw,
        shieldFrame.sh,
        -SHIELD_RENDER_WIDTH / 2,
        -SHIELD_RENDER_HEIGHT / 2,
        SHIELD_RENDER_WIDTH,
        SHIELD_RENDER_HEIGHT
      );
    }
  }

  if (shieldRegenPulse) {
    const shieldBaseRadius = (Math.min(SHIELD_RENDER_WIDTH, SHIELD_RENDER_HEIGHT) / 2) * 0.48;
    const pulseRadius = shieldBaseRadius * (0.97 + (0.1 * shieldRegenPulse.progress));
    context.save();
    context.globalAlpha = 0.75 * (1 - shieldRegenPulse.progress);
    context.strokeStyle = '#bfe4ff';
    context.lineWidth = 3.2 - (1.2 * shieldRegenPulse.progress);
    context.beginPath();
    context.arc(0, 0, pulseRadius, 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }
  if (invulnerable) {
    const ringRadius = (Math.min(SHIELD_RENDER_WIDTH, SHIELD_RENDER_HEIGHT) / 2) * 0.48;
    context.save();
    context.strokeStyle = '#f97316';
    context.lineWidth = 3.2;
    context.globalAlpha = 0.9;
    context.beginPath();
    context.arc(0, 0, ringRadius, 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }
  context.restore();

  if (showHitbox) {
    context.save();
    context.strokeStyle = 'rgba(34, 197, 94, 0.7)';
    context.lineWidth = 2;
    context.beginPath();
    context.arc(x, y, arenaRadiusToCanvasRadius(playerHitRadius), 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }

  const lifeRatio = Math.max(0, (hitsToDie - Number(player.damage_taken || 0)) / Math.max(1, hitsToDie));
  const shieldRatio = shieldPoints > 0 ? Number(player.shield_points || 0) / Math.max(1, shieldPoints) : 0;
  drawRectHealthBar(x, y - 67, 56, 7, shieldRatio, '#60a5fa');
  drawRectHealthBar(x, y - 57, 56, 7, lifeRatio, '#22c55e');

  const displayName = String(player.username || '').trim() || `#${player.user_id}`;
  context.save();
  context.font = '600 14px Arial';
  context.textAlign = 'center';
  context.textBaseline = 'bottom';
  context.lineWidth = 4;
  context.strokeStyle = 'rgba(15, 23, 42, 0.9)';
  context.fillStyle = '#f8fafc';
  context.strokeText(displayName, x, y - 33);
  context.fillText(displayName, x, y - 33);
  context.restore();
  if (invulnerable) {
    context.save();
    context.font = '700 13px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'bottom';
    context.lineWidth = 4;
    context.strokeStyle = 'rgba(15, 23, 42, 0.95)';
    context.fillStyle = '#f97316';
    context.strokeText('Invulnerável', x, y - 78);
    context.fillText('Invulnerável', x, y - 78);
    context.restore();
  }
}

function addFloatingTextForPlayer(userId, text, color, durationMs = 900) {
  floatingTexts.push({
    text,
    color,
    followUserId: Number(userId),
    createdAt: performance.now(),
    durationMs: Math.max(120, durationMs),
    offsetArenaY: -8,
  });
}

function addFloatingTextAtArena(x, y, text, color, durationMs = 1100) {
  floatingTexts.push({
    text,
    color,
    followUserId: null,
    x: Number(x),
    y: Number(y),
    createdAt: performance.now(),
    durationMs: Math.max(120, durationMs),
  });
}

function drawFloatingTexts() {
  if (!floatingTexts.length) return;
  const now = performance.now();
  for (let i = floatingTexts.length - 1; i >= 0; i -= 1) {
    const entry = floatingTexts[i];
    const elapsed = now - entry.createdAt;
    if (elapsed >= entry.durationMs) {
      floatingTexts.splice(i, 1);
      continue;
    }

    let x;
    let y;
    if (entry.followUserId !== null) {
      const target = findPlayerByUserId(worldState, entry.followUserId);
      if (!target || !target.alive) {
        floatingTexts.splice(i, 1);
        continue;
      }
      x = arenaToCanvasX(target.x);
      y = arenaToCanvasY(target.y + entry.offsetArenaY);
    } else {
      x = arenaToCanvasX(entry.x);
      y = arenaToCanvasY(entry.y);
    }

    const t = elapsed / entry.durationMs;
    const risePx = 22 * t;
    context.save();
    context.globalAlpha = 1 - t;
    context.font = '700 24px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'bottom';
    context.lineWidth = 5;
    context.strokeStyle = 'rgba(15, 23, 42, 0.9)';
    context.fillStyle = entry.color;
    context.strokeText(entry.text, x, y - risePx);
    context.fillText(entry.text, x, y - risePx);
    context.restore();
  }
}

function triggerShieldRegenEffects(previousSnapshot, currentSnapshot) {
  if (!previousSnapshot || !currentSnapshot) return;
  const previousById = new Map(
    (previousSnapshot.players || []).map((player) => [Number(player.user_id), player])
  );
  for (const currentPlayer of (currentSnapshot.players || [])) {
    const previousPlayer = previousById.get(Number(currentPlayer.user_id));
    if (!previousPlayer) continue;
    const previousShield = Math.max(0, Math.floor(Number(previousPlayer.shield_points ?? 0)));
    const currentShield = Math.max(0, Math.floor(Number(currentPlayer.shield_points ?? 0)));
    if (currentShield > previousShield) setShieldRegenPulse(currentPlayer.user_id);
  }
}

function render() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#17324f';
  context.fillRect(0, 0, canvas.width, canvas.height);
  if (worldState) {
    for (const mine of (worldState.mines || [])) {
      knownMinePositions.set(Number(mine.mine_id), { x: Number(mine.x), y: Number(mine.y) });
    }
    (worldState.obstacles || []).forEach(drawObstacle);
    (worldState.mines || []).forEach(drawMine);
    (worldState.players || []).forEach(drawPlayer);
    (worldState.projectiles || []).forEach(drawProjectile);
  }
  drawFloatingTexts();
  requestAnimationFrame(render);
}

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
  if (resizeHandle !== null) cancelAnimationFrame(resizeHandle);
  resizeHandle = requestAnimationFrame(() => {
    resizeHandle = null;
    applyCanvasScale();
  });
}

async function fetchSession() {
  const mode = encodeURIComponent(window.DK_SESSION.gameMode || 'open_world');
  const endpoint = `${window.DK_SESSION.sessionEndpoint}?mode=${mode}&_=${Date.now()}`;
  const response = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' });
  const data = await response.json();
  if (!data.ok) {
    window.location.href = '/index.php?page=login';
    return null;
  }
  myUserId = data.user_id;
  if (typeof data.mine_cooldown_ticks === 'number') mineCooldownTicks = Math.max(1, Math.floor(data.mine_cooldown_ticks));
  if (typeof data.hits_to_win === 'number') hitsToDie = Math.max(1, Math.floor(data.hits_to_win));
  if (typeof data.mine_hits_to_destroy === 'number') mineHitsToDestroy = Math.max(1, Math.floor(data.mine_hits_to_destroy));
  if (typeof data.shield_points === 'number') shieldPoints = Math.max(0, Math.floor(data.shield_points));
  if (typeof data.shield_regen_seconds === 'number') shieldRegenSeconds = Math.max(1, Math.floor(data.shield_regen_seconds));
  if (typeof data.player_hitbox_radius === 'number') playerHitRadius = Math.max(0.1, data.player_hitbox_radius);
  if (typeof data.projectile_hitbox_radius === 'number') projectileHitRadius = Math.max(0.1, data.projectile_hitbox_radius);
  if (typeof data.mine_hitbox_radius === 'number') mineHitRadius = Math.max(0.1, data.mine_hitbox_radius);
  if (typeof data.show_hitbox === 'boolean') showHitbox = data.show_hitbox;
  return data;
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
      statusNode.textContent = `Conectado como ${payload.username}`;
      send('open_world_join');
      return;
    }

    if (event === 'open_world_joined') {
      if (typeof payload.tick_rate === 'number') matchTickRate = Math.max(1, Math.floor(payload.tick_rate));
      statusNode.textContent = 'Mundo aberto online';
      return;
    }

    if (event === 'open_world_state') {
      const previousSnapshot = worldState;
      worldState = payload;
      triggerShieldRegenEffects(previousSnapshot, payload);
      updateDeathOverlay();
      updateHud();
      return;
    }

    if (event === 'open_world_hit') {
      const attackerId = Number(payload.attacker);
      const targetId = Number(payload.target);
      const myHit = attackerId === Number(myUserId);
      const shieldBlocked = Boolean(payload.shield_blocked);
      if (shieldBlocked) setPlayerFlash(targetId, '#bfe4ff', 180, 'shield');
      else setPlayerFlash(targetId, myHit ? '#86efac' : '#fca5a5');
      applyPlayerKnockback(attackerId, targetId);
      addFloatingTextForPlayer(targetId, shieldBlocked ? 'Block!' : 'Hit!', shieldBlocked ? '#93c5fd' : '#f8fafc');
      return;
    }

    if (event === 'open_world_mine_hit') {
      const attackerId = Number(payload.attacker);
      const mineOwnerId = Number(payload.mine_owner);
      const mineId = Number(payload.mine_id);
      const destroyed = Boolean(payload.destroyed);
      const myHit = attackerId === Number(myUserId);
      const myMineHit = mineOwnerId === Number(myUserId);
      if (myHit) {
        setMineFlash(mineId, '#86efac');
      } else if (myMineHit) {
        setMineFlash(mineId, '#fca5a5');
      }
      const minePos = knownMinePositions.get(mineId);
      if (minePos) {
        if (destroyed) {
          addFloatingTextAtArena(minePos.x, minePos.y, 'Mina destruida!', '#f59e0b');
          knownMinePositions.delete(mineId);
        } else {
          addFloatingTextAtArena(minePos.x, minePos.y, 'Hit!', '#f8fafc', 800);
        }
      }
      return;
    }

    if (event === 'open_world_death') {
      const targetId = Number(payload.target_id);
      const target = findPlayerByUserId(worldState, targetId);
      if (target) {
        addFloatingTextAtArena(Number(target.x), Number(target.y), 'Kill!', '#ef4444', 1100);
      }
      if (targetId === Number(myUserId)) statusNode.textContent = 'Voce foi destruido';
      return;
    }

    if (event === 'open_world_respawned') {
      const invulSeconds = Math.max(1, Number(payload.invulnerable_seconds || 2));
      statusNode.textContent = `Renascido (invulneravel por ${invulSeconds}s)`;
      return;
    }

    if (event === 'error') {
      statusNode.textContent = `${payload.code}: ${payload.message}`;
    }
  });

  ws.addEventListener('close', () => {
    statusNode.textContent = 'Conexao encerrada';
  });
}

window.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') pressed.left = true;
  if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') pressed.right = true;
  if (event.key === 'ArrowUp' || event.key.toLowerCase() === 'w') pressed.up = true;
  if (event.key === 'ArrowDown' || event.key.toLowerCase() === 's') pressed.down = true;
  if ((event.code === 'Digit1' || event.code === 'Numpad1' || event.key === '1') && !event.repeat) {
    event.preventDefault();
    pendingMine = false;
    send('drop_mine');
  }
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
  if (isSelfInvulnerable()) return;
  syncPointerFromEvent(event);
  pendingShot = true;
  scheduleInput();
});

respawnButton.addEventListener('click', () => {
  send('open_world_respawn');
});

window.addEventListener('resize', scheduleCanvasScale);
window.addEventListener('orientationchange', scheduleCanvasScale);
scheduleCanvasScale();
connect();
render();
