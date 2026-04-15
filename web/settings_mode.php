<?php

declare(strict_types=1);

$user = require_admin();
ensure_admin_schema();

if (!isset($settingsMode, $settingsTitle, $settingsLabel)) {
    throw new RuntimeException('settings mode not defined');
}

$modePrefix = $settingsMode === 'open_world' ? 'open_world_' : '1v1_';
$success = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        if (isset($_POST['save_settings'])) {
            $projectileSpeed = (float) ($_POST['projectile_speed'] ?? 1.6);
            $movementSpeed = (float) ($_POST['movement_speed'] ?? 3.0);
            $hitsToWin = (int) ($_POST['hits_to_win'] ?? 3);
            $fireCooldownTicks = (int) ($_POST['fire_cooldown_ticks'] ?? 6);
            $attackRange = (float) ($_POST['attack_range'] ?? 22);
            $mineCooldownTicks = (int) ($_POST['mine_cooldown_ticks'] ?? 100);
            $mineMaxActivePerPlayer = (int) ($_POST['mine_max_active_per_player'] ?? 3);
            $wsMode = (string) ($_POST['ws_mode'] ?? 'vps');
            $renderSmoothing = (float) ($_POST['render_smoothing'] ?? 0.25);
            $playerHitboxRadius = (float) ($_POST['player_hitbox_radius'] ?? 5.4);
            $projectileHitboxRadius = (float) ($_POST['projectile_hitbox_radius'] ?? 0.6);
            $mineHitboxRadius = (float) ($_POST['mine_hitbox_radius'] ?? 2.4);
            $mineHitsToDestroy = (int) ($_POST['mine_hits_to_destroy'] ?? 2);
            $shieldPoints = (int) ($_POST['shield_points'] ?? 2);
            $shieldRegenSeconds = (int) ($_POST['shield_regen_seconds'] ?? 10);
            $respawnInvulnerabilitySeconds = (int) ($_POST['respawn_invulnerability_seconds'] ?? 2);
            $monsterMaxAlive = (int) ($_POST['monster_max_alive'] ?? 8);
            $monsterLife = (int) ($_POST['monster_life'] ?? 6);
            $monsterMoveSpeed = (float) ($_POST['monster_move_speed'] ?? 1.2);
            $monsterProjectileSpeed = (float) ($_POST['monster_projectile_speed'] ?? 1.1);
            $monsterFireCooldownTicks = (int) ($_POST['monster_fire_cooldown_ticks'] ?? 35);
            $monsterRespawnSeconds = (int) ($_POST['monster_respawn_seconds'] ?? 5);
            $showHitbox = isset($_POST['show_hitbox']) ? 1 : 0;

            if (
                $projectileSpeed <= 0
                || $movementSpeed <= 0
                || $hitsToWin <= 0
                || $fireCooldownTicks <= 0
                || $attackRange <= 0
                || $mineCooldownTicks <= 0
                || $mineMaxActivePerPlayer <= 0
                || !in_array($wsMode, ['vps', 'local'], true)
                || $renderSmoothing < 0
                || $renderSmoothing > 1
                || $playerHitboxRadius <= 0
                || $projectileHitboxRadius <= 0
                || $mineHitboxRadius <= 0
                || $mineHitsToDestroy <= 0
                || $shieldPoints < 0
                || $shieldRegenSeconds <= 0
                || $respawnInvulnerabilitySeconds <= 0
                || $monsterMaxAlive < 0
                || $monsterLife <= 0
                || $monsterMoveSpeed <= 0
                || $monsterProjectileSpeed <= 0
                || $monsterFireCooldownTicks <= 0
                || $monsterRespawnSeconds <= 0
            ) {
                throw new RuntimeException('Valores invalidos');
            }

            $stmt = db()->prepare(
                'INSERT INTO game_settings (setting_key, setting_value)
                 VALUES (:setting_key, :setting_value)
                 ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)'
            );
            $stmt->execute(['setting_key' => $modePrefix . 'projectile_speed', 'setting_value' => (string) $projectileSpeed]);
            $stmt->execute(['setting_key' => $modePrefix . 'movement_speed', 'setting_value' => (string) $movementSpeed]);
            $stmt->execute(['setting_key' => $modePrefix . 'hits_to_win', 'setting_value' => (string) $hitsToWin]);
            $stmt->execute(['setting_key' => $modePrefix . 'fire_cooldown_ticks', 'setting_value' => (string) $fireCooldownTicks]);
            $stmt->execute(['setting_key' => $modePrefix . 'attack_range', 'setting_value' => (string) $attackRange]);
            $stmt->execute(['setting_key' => $modePrefix . 'mine_cooldown_ticks', 'setting_value' => (string) $mineCooldownTicks]);
            $stmt->execute([
                'setting_key' => $modePrefix . 'mine_max_active_per_player',
                'setting_value' => (string) $mineMaxActivePerPlayer,
            ]);
            $stmt->execute(['setting_key' => $modePrefix . 'render_smoothing', 'setting_value' => (string) $renderSmoothing]);
            $stmt->execute(['setting_key' => $modePrefix . 'player_hitbox_radius', 'setting_value' => (string) $playerHitboxRadius]);
            $stmt->execute(['setting_key' => $modePrefix . 'projectile_hitbox_radius', 'setting_value' => (string) $projectileHitboxRadius]);
            $stmt->execute(['setting_key' => $modePrefix . 'mine_hitbox_radius', 'setting_value' => (string) $mineHitboxRadius]);
            $stmt->execute(['setting_key' => $modePrefix . 'mine_hits_to_destroy', 'setting_value' => (string) $mineHitsToDestroy]);
            $stmt->execute(['setting_key' => $modePrefix . 'shield_points', 'setting_value' => (string) $shieldPoints]);
            $stmt->execute(['setting_key' => $modePrefix . 'shield_regen_seconds', 'setting_value' => (string) $shieldRegenSeconds]);
            $stmt->execute([
                'setting_key' => $modePrefix . 'respawn_invulnerability_seconds',
                'setting_value' => (string) $respawnInvulnerabilitySeconds,
            ]);
            $stmt->execute(['setting_key' => $modePrefix . 'monster_max_alive', 'setting_value' => (string) $monsterMaxAlive]);
            $stmt->execute(['setting_key' => $modePrefix . 'monster_life', 'setting_value' => (string) $monsterLife]);
            $stmt->execute(['setting_key' => $modePrefix . 'monster_move_speed', 'setting_value' => (string) $monsterMoveSpeed]);
            $stmt->execute(['setting_key' => $modePrefix . 'monster_projectile_speed', 'setting_value' => (string) $monsterProjectileSpeed]);
            $stmt->execute(['setting_key' => $modePrefix . 'monster_fire_cooldown_ticks', 'setting_value' => (string) $monsterFireCooldownTicks]);
            $stmt->execute(['setting_key' => $modePrefix . 'monster_respawn_seconds', 'setting_value' => (string) $monsterRespawnSeconds]);
            $stmt->execute(['setting_key' => $modePrefix . 'show_hitbox', 'setting_value' => (string) $showHitbox]);
            $stmt->execute(['setting_key' => 'ws_mode', 'setting_value' => $wsMode]);
            $success = 'Configuracoes salvas';
        }
    } catch (Throwable $throwable) {
        $error = $throwable->getMessage();
    }
}

$settingsRows = db()->query('SELECT setting_key, setting_value FROM game_settings')->fetchAll();
$settings = [];
foreach ($settingsRows as $row) {
    $settings[$row['setting_key']] = $row['setting_value'];
}

$getSetting = static function (string $key, string $default) use ($settings, $modePrefix): string {
    $prefixedKey = $modePrefix . $key;
    if (array_key_exists($prefixedKey, $settings)) {
        return (string) $settings[$prefixedKey];
    }
    if (array_key_exists($key, $settings)) {
        return (string) $settings[$key];
    }
    return $default;
};

render_header($settingsTitle);
?>
<section class="grid">
    <div class="panel">
        <h1>Configurações <?= htmlspecialchars($settingsLabel, ENT_QUOTES, 'UTF-8') ?></h1>
        <div class="row">
            <a href="/index.php?page=settings">Voltar</a>
            <a href="/index.php?page=settings_1v1">1v1</a>
            <a href="/index.php?page=settings_openworld">Mundo Aberto</a>
        </div>
        <?php if ($success !== null): ?>
            <div class="success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
        <?php endif; ?>
        <?php if ($error !== null): ?>
            <div class="alert"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
        <?php endif; ?>
        <form method="post" class="settings-compact-form">
            <div class="settings-columns">
                <div class="settings-col">
                    <h2>Movimento E Rede</h2>
                    <label>
                        <span>Velocidade de movimento</span>
                        <input type="number" step="0.1" min="0.1" name="movement_speed" value="<?= htmlspecialchars($getSetting('movement_speed', '3.0'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>WebSocket ativo</span>
                        <select name="ws_mode" required>
                            <?php $wsModeSelected = (string) ($settings['ws_mode'] ?? 'vps'); ?>
                            <option value="vps" <?= $wsModeSelected === 'vps' ? 'selected' : '' ?>>VPS</option>
                            <option value="local" <?= $wsModeSelected === 'local' ? 'selected' : '' ?>>Local</option>
                        </select>
                    </label>

                    <h2>Combate Base</h2>
                    <label>
                        <span>Vida (acertos)</span>
                        <input type="number" step="1" min="1" name="hits_to_win" value="<?= htmlspecialchars($getSetting('hits_to_win', '3'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Velocidade de projetil</span>
                        <input type="number" step="0.1" min="0.1" name="projectile_speed" value="<?= htmlspecialchars($getSetting('projectile_speed', '1.6'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Intervalo entre disparos por clique (ticks)</span>
                        <input type="number" step="1" min="1" name="fire_cooldown_ticks" value="<?= htmlspecialchars($getSetting('fire_cooldown_ticks', '6'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Range de disparo</span>
                        <input type="number" step="0.1" min="0.1" name="attack_range" value="<?= htmlspecialchars($getSetting('attack_range', '22'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>

                    <h2>Minas</h2>
                    <label>
                        <span>Cooldown da mina (ticks)</span>
                        <input type="number" step="1" min="1" name="mine_cooldown_ticks" value="<?= htmlspecialchars($getSetting('mine_cooldown_ticks', '100'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Maximo simultaneo por player</span>
                        <input type="number" step="1" min="1" name="mine_max_active_per_player" value="<?= htmlspecialchars($getSetting('mine_max_active_per_player', '3'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Hits para destruir mina</span>
                        <input type="number" step="1" min="1" name="mine_hits_to_destroy" value="<?= htmlspecialchars($getSetting('mine_hits_to_destroy', '2'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                </div>

                <div class="settings-col">
                    <h2>Escudo E Respawn</h2>
                    <label>
                        <span>Pontos de escudo</span>
                        <input type="number" step="1" min="0" name="shield_points" value="<?= htmlspecialchars($getSetting('shield_points', '2'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Tempo para regenerar 1 escudo (segundos)</span>
                        <input type="number" step="1" min="1" name="shield_regen_seconds" value="<?= htmlspecialchars($getSetting('shield_regen_seconds', '10'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Invulnerabilidade ao renascer (segundos)</span>
                        <input type="number" step="1" min="1" name="respawn_invulnerability_seconds" value="<?= htmlspecialchars($getSetting('respawn_invulnerability_seconds', '2'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>

                    <h2>Visual E Colisão</h2>
                    <label>
                        <span>Suavizacao visual (0-1)</span>
                        <input type="number" step="0.01" min="0" max="1" name="render_smoothing" value="<?= htmlspecialchars($getSetting('render_smoothing', '0.25'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Hitbox da nave</span>
                        <input type="number" step="0.1" min="0.1" name="player_hitbox_radius" value="<?= htmlspecialchars($getSetting('player_hitbox_radius', '5.4'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Hitbox do projetil</span>
                        <input type="number" step="0.1" min="0.1" name="projectile_hitbox_radius" value="<?= htmlspecialchars($getSetting('projectile_hitbox_radius', '0.6'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Hitbox da mina</span>
                        <input type="number" step="0.1" min="0.1" name="mine_hitbox_radius" value="<?= htmlspecialchars($getSetting('mine_hitbox_radius', '2.4'), ENT_QUOTES, 'UTF-8') ?>" required>
                    </label>
                    <label>
                        <span>Mostrar linha de hitbox</span>
                        <input type="checkbox" name="show_hitbox" value="1" <?= ($getSetting('show_hitbox', '1') === '1') ? 'checked' : '' ?>>
                    </label>
                </div>

                <div class="settings-col">
                    <?php if ($settingsMode === 'open_world'): ?>
                        <h2>Monstros (Mundo Aberto)</h2>
                        <label>
                            <span>Máximo simultâneo</span>
                            <input type="number" step="1" min="0" name="monster_max_alive" value="<?= htmlspecialchars($getSetting('monster_max_alive', '8'), ENT_QUOTES, 'UTF-8') ?>" required>
                        </label>
                        <label>
                            <span>Vida do monstro</span>
                            <input type="number" step="1" min="1" name="monster_life" value="<?= htmlspecialchars($getSetting('monster_life', '6'), ENT_QUOTES, 'UTF-8') ?>" required>
                        </label>
                        <label>
                            <span>Velocidade de movimento</span>
                            <input type="number" step="0.1" min="0.1" name="monster_move_speed" value="<?= htmlspecialchars($getSetting('monster_move_speed', '1.2'), ENT_QUOTES, 'UTF-8') ?>" required>
                        </label>
                        <label>
                            <span>Velocidade do projetil</span>
                            <input type="number" step="0.1" min="0.1" name="monster_projectile_speed" value="<?= htmlspecialchars($getSetting('monster_projectile_speed', '1.1'), ENT_QUOTES, 'UTF-8') ?>" required>
                        </label>
                        <label>
                            <span>Intervalo entre tiros (ticks)</span>
                            <input type="number" step="1" min="1" name="monster_fire_cooldown_ticks" value="<?= htmlspecialchars($getSetting('monster_fire_cooldown_ticks', '35'), ENT_QUOTES, 'UTF-8') ?>" required>
                        </label>
                        <label>
                            <span>Respawn do monstro (segundos)</span>
                            <input type="number" step="1" min="1" name="monster_respawn_seconds" value="<?= htmlspecialchars($getSetting('monster_respawn_seconds', '5'), ENT_QUOTES, 'UTF-8') ?>" required>
                        </label>
                    <?php endif; ?>
                </div>
            </div>
            <button class="settings-save-btn" type="submit" name="save_settings" value="1">Salvar</button>
        </form>
    </div>
</section>
<?php render_footer(); ?>
