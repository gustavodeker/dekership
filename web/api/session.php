<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
header('Expires: 0');

$user = current_user();
if ($user === null) {
    http_response_code(401);
    echo json_encode(['ok' => false, 'message' => 'unauthorized']);
    exit;
}

$config = app_config();
$sql = sprintf(
    'SELECT %s AS token FROM %s WHERE %s = :user_id LIMIT 1',
    $config['auth_token_column'],
    $config['auth_user_table'],
    $config['auth_id_column']
);
$stmt = db()->prepare($sql);
$stmt->execute(['user_id' => (int) $user['user_id']]);
$freshToken = $stmt->fetchColumn();
if (!is_string($freshToken) || $freshToken === '') {
    http_response_code(401);
    echo json_encode(['ok' => false, 'message' => 'invalid_token']);
    exit;
}

$_SESSION['auth_user']['token'] = $freshToken;

$renderSmoothing = 0.25;
$playerHitboxRadius = 5.4;
$projectileHitboxRadius = 0.6;
$mineHitboxRadius = 2.4;
$mineCooldownTicks = 100;
$hitsToWin = 3;
$mineHitsToDestroy = 2;
$shieldPoints = 2;
$shieldRegenSeconds = 10;
$showHitbox = true;
$wsMode = 'vps';
try {
    $settingStmt = db()->prepare(
        "SELECT setting_key, setting_value
         FROM game_settings
         WHERE setting_key IN ('render_smoothing', 'player_hitbox_radius', 'projectile_hitbox_radius', 'mine_hitbox_radius', 'mine_cooldown_ticks', 'hits_to_win', 'mine_hits_to_destroy', 'shield_points', 'shield_regen_seconds', 'show_hitbox', 'ws_mode')"
    );
    $settingStmt->execute();
    $settings = $settingStmt->fetchAll(PDO::FETCH_KEY_PAIR);
    if (isset($settings['render_smoothing'])) {
        $renderSmoothing = (float) $settings['render_smoothing'];
    }
    if (isset($settings['player_hitbox_radius'])) {
        $playerHitboxRadius = (float) $settings['player_hitbox_radius'];
    }
    if (isset($settings['projectile_hitbox_radius'])) {
        $projectileHitboxRadius = (float) $settings['projectile_hitbox_radius'];
    }
    if (isset($settings['mine_hitbox_radius'])) {
        $mineHitboxRadius = (float) $settings['mine_hitbox_radius'];
    }
    if (isset($settings['mine_cooldown_ticks'])) {
        $mineCooldownTicks = (int) (float) $settings['mine_cooldown_ticks'];
    }
    if (isset($settings['hits_to_win'])) {
        $hitsToWin = (int) (float) $settings['hits_to_win'];
    }
    if (isset($settings['mine_hits_to_destroy'])) {
        $mineHitsToDestroy = (int) (float) $settings['mine_hits_to_destroy'];
    }
    if (isset($settings['shield_points'])) {
        $shieldPoints = (int) (float) $settings['shield_points'];
    }
    if (isset($settings['shield_regen_seconds'])) {
        $shieldRegenSeconds = (int) (float) $settings['shield_regen_seconds'];
    }
    if (isset($settings['show_hitbox'])) {
        $showHitbox = (string) $settings['show_hitbox'] !== '0';
    }
    if (isset($settings['ws_mode'])) {
        $candidateWsMode = (string) $settings['ws_mode'];
        if (in_array($candidateWsMode, ['vps', 'local'], true)) {
            $wsMode = $candidateWsMode;
        }
    }
} catch (Throwable $throwable) {
    $renderSmoothing = 0.25;
    $playerHitboxRadius = 5.4;
    $projectileHitboxRadius = 0.6;
    $mineHitboxRadius = 2.4;
    $mineCooldownTicks = 100;
    $hitsToWin = 3;
    $mineHitsToDestroy = 2;
    $shieldPoints = 2;
    $shieldRegenSeconds = 10;
    $showHitbox = true;
    $wsMode = 'vps';
}
$renderSmoothing = max(0.0, min(1.0, $renderSmoothing));
$playerHitboxRadius = max(0.1, $playerHitboxRadius);
$projectileHitboxRadius = max(0.1, $projectileHitboxRadius);
$mineHitboxRadius = max(0.1, $mineHitboxRadius);
$mineCooldownTicks = max(1, $mineCooldownTicks);
$hitsToWin = max(1, $hitsToWin);
$mineHitsToDestroy = max(1, $mineHitsToDestroy);
$shieldPoints = max(0, $shieldPoints);
$shieldRegenSeconds = max(1, $shieldRegenSeconds);
$configData = app_config();
$wsUrl = $wsMode === 'local'
    ? (string) $configData['ws_url_local']
    : (string) $configData['ws_url_vps'];

echo json_encode([
    'ok' => true,
    'user_id' => $user['user_id'],
    'username' => $user['username'],
    'display_name' => $user['display_name'],
    'token' => $freshToken,
    'render_smoothing' => $renderSmoothing,
    'player_hitbox_radius' => $playerHitboxRadius,
    'projectile_hitbox_radius' => $projectileHitboxRadius,
    'mine_hitbox_radius' => $mineHitboxRadius,
    'mine_cooldown_ticks' => $mineCooldownTicks,
    'hits_to_win' => $hitsToWin,
    'mine_hits_to_destroy' => $mineHitsToDestroy,
    'shield_points' => $shieldPoints,
    'shield_regen_seconds' => $shieldRegenSeconds,
    'show_hitbox' => $showHitbox,
    'ws_mode' => $wsMode,
    'ws_url' => $wsUrl,
], JSON_UNESCAPED_SLASHES);

