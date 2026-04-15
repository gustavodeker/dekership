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
$mineMaxActivePerPlayer = 3;
$attackRange = 22.0;
$hitsToWin = 3;
$mineHitsToDestroy = 2;
$shieldPoints = 2;
$shieldRegenSeconds = 10;
$showHitbox = true;
$wsMode = 'vps';
$mode = (string) ($_GET['mode'] ?? '1v1');
if (!in_array($mode, ['1v1', 'open_world'], true)) {
    $mode = '1v1';
}
$prefix = $mode === 'open_world' ? 'open_world_' : '1v1_';
try {
    $settingStmt = db()->query("SELECT setting_key, setting_value FROM game_settings");
    $settings = $settingStmt->fetchAll(PDO::FETCH_KEY_PAIR);
    $readModeSetting = static function (string $key, string $default) use ($settings, $prefix): string {
        $prefixedKey = $prefix . $key;
        if (isset($settings[$prefixedKey])) {
            return (string) $settings[$prefixedKey];
        }
        if (isset($settings[$key])) {
            return (string) $settings[$key];
        }
        return $default;
    };
    $renderSmoothing = (float) $readModeSetting('render_smoothing', '0.25');
    $playerHitboxRadius = (float) $readModeSetting('player_hitbox_radius', '5.4');
    $projectileHitboxRadius = (float) $readModeSetting('projectile_hitbox_radius', '0.6');
    $mineHitboxRadius = (float) $readModeSetting('mine_hitbox_radius', '2.4');
    $mineCooldownTicks = (int) (float) $readModeSetting('mine_cooldown_ticks', '100');
    $mineMaxActivePerPlayer = (int) (float) $readModeSetting('mine_max_active_per_player', '3');
    $attackRange = (float) $readModeSetting('attack_range', '22');
    $hitsToWin = (int) (float) $readModeSetting('hits_to_win', '3');
    $mineHitsToDestroy = (int) (float) $readModeSetting('mine_hits_to_destroy', '2');
    $shieldPoints = (int) (float) $readModeSetting('shield_points', '2');
    $shieldRegenSeconds = (int) (float) $readModeSetting('shield_regen_seconds', '10');
    $showHitbox = $readModeSetting('show_hitbox', '1') !== '0';
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
    $mineMaxActivePerPlayer = 3;
    $attackRange = 22.0;
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
$mineMaxActivePerPlayer = max(1, $mineMaxActivePerPlayer);
$attackRange = max(0.1, $attackRange);
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
    'mine_max_active_per_player' => $mineMaxActivePerPlayer,
    'attack_range' => $attackRange,
    'hits_to_win' => $hitsToWin,
    'mine_hits_to_destroy' => $mineHitsToDestroy,
    'shield_points' => $shieldPoints,
    'shield_regen_seconds' => $shieldRegenSeconds,
    'show_hitbox' => $showHitbox,
    'mode' => $mode,
    'ws_mode' => $wsMode,
    'ws_url' => $wsUrl,
], JSON_UNESCAPED_SLASHES);

