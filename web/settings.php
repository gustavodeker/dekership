<?php

declare(strict_types=1);

$user = require_admin();
ensure_admin_schema();

$success = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        if (isset($_POST['save_settings'])) {
            $projectileSpeed = (float) ($_POST['projectile_speed'] ?? 1.6);
            $movementSpeed = (float) ($_POST['movement_speed'] ?? 3.0);
            $hitsToWin = (int) ($_POST['hits_to_win'] ?? 3);
            $fireCooldownTicks = (int) ($_POST['fire_cooldown_ticks'] ?? 6);
            $renderSmoothing = (float) ($_POST['render_smoothing'] ?? 0.25);
            $playerHitboxRadius = (float) ($_POST['player_hitbox_radius'] ?? 5.4);
            $projectileHitboxRadius = (float) ($_POST['projectile_hitbox_radius'] ?? 0.6);
            $showHitbox = isset($_POST['show_hitbox']) ? 1 : 0;

            if (
                $projectileSpeed <= 0
                || $movementSpeed <= 0
                || $hitsToWin <= 0
                || $fireCooldownTicks <= 0
                || $renderSmoothing < 0
                || $renderSmoothing > 1
                || $playerHitboxRadius <= 0
                || $projectileHitboxRadius <= 0
            ) {
                throw new RuntimeException('Valores invalidos');
            }

            $stmt = db()->prepare(
                'INSERT INTO game_settings (setting_key, setting_value)
                 VALUES (:setting_key, :setting_value)
                 ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)'
            );
            $stmt->execute(['setting_key' => 'projectile_speed', 'setting_value' => (string) $projectileSpeed]);
            $stmt->execute(['setting_key' => 'movement_speed', 'setting_value' => (string) $movementSpeed]);
            $stmt->execute(['setting_key' => 'hits_to_win', 'setting_value' => (string) $hitsToWin]);
            $stmt->execute(['setting_key' => 'fire_cooldown_ticks', 'setting_value' => (string) $fireCooldownTicks]);
            $stmt->execute(['setting_key' => 'render_smoothing', 'setting_value' => (string) $renderSmoothing]);
            $stmt->execute(['setting_key' => 'player_hitbox_radius', 'setting_value' => (string) $playerHitboxRadius]);
            $stmt->execute(['setting_key' => 'projectile_hitbox_radius', 'setting_value' => (string) $projectileHitboxRadius]);
            $stmt->execute(['setting_key' => 'show_hitbox', 'setting_value' => (string) $showHitbox]);
            $success = 'Configuracoes salvas';
        }

        if (isset($_POST['toggle_admin'])) {
            $targetUserId = (int) ($_POST['target_user_id'] ?? 0);
            $makeAdmin = (int) ($_POST['make_admin'] ?? 0) === 1;

            if ($targetUserId <= 0) {
                throw new RuntimeException('Usuario invalido');
            }

            if ($makeAdmin) {
                db()->prepare(
                    'INSERT INTO game_admin (user_id, granted_by_user_id)
                     VALUES (:user_id, :granted_by_user_id)
                     ON DUPLICATE KEY UPDATE granted_by_user_id = VALUES(granted_by_user_id)'
                )->execute([
                    'user_id' => $targetUserId,
                    'granted_by_user_id' => $user['user_id'],
                ]);
            } else {
                if ($targetUserId === (int) $user['user_id']) {
                    throw new RuntimeException('Voce nao pode remover seu proprio admin');
                }
                db()->prepare('DELETE FROM game_admin WHERE user_id = :user_id')->execute(['user_id' => $targetUserId]);
            }

            $success = 'Permissao atualizada';
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

$config = app_config();
$sql = sprintf(
    'SELECT u.%1$s AS user_id, u.%2$s AS username, u.email,
            CASE WHEN ga.user_id IS NULL THEN 0 ELSE 1 END AS is_admin
     FROM %3$s u
     LEFT JOIN game_admin ga ON ga.user_id = u.%1$s
     ORDER BY u.%2$s ASC',
    $config['auth_id_column'],
    $config['auth_username_column'],
    $config['auth_user_table']
);
$users = db()->query($sql)->fetchAll();

render_header('Configuracoes');
?>
<section class="grid">
    <div class="panel">
        <h1>Configuracoes do jogo</h1>
        <?php if ($success !== null): ?>
            <div class="success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
        <?php endif; ?>
        <?php if ($error !== null): ?>
            <div class="alert"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
        <?php endif; ?>
        <form method="post" class="stack">
            <label>
                <span>Velocidade de projetil</span>
                <input type="number" step="0.1" min="0.1" name="projectile_speed" value="<?= htmlspecialchars((string) ($settings['projectile_speed'] ?? '1.6'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Velocidade de movimento</span>
                <input type="number" step="0.1" min="0.1" name="movement_speed" value="<?= htmlspecialchars((string) ($settings['movement_speed'] ?? '3.0'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Vida (acertos para vencer)</span>
                <input type="number" step="1" min="1" name="hits_to_win" value="<?= htmlspecialchars((string) ($settings['hits_to_win'] ?? '3'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Intervalo entre disparos por clique (ticks)</span>
                <input type="number" step="1" min="1" name="fire_cooldown_ticks" value="<?= htmlspecialchars((string) ($settings['fire_cooldown_ticks'] ?? '6'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Suavizacao visual (0-1)</span>
                <input type="number" step="0.01" min="0" max="1" name="render_smoothing" value="<?= htmlspecialchars((string) ($settings['render_smoothing'] ?? '0.25'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Hitbox da nave</span>
                <input type="number" step="0.1" min="0.1" name="player_hitbox_radius" value="<?= htmlspecialchars((string) ($settings['player_hitbox_radius'] ?? '5.4'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Hitbox do projetil</span>
                <input type="number" step="0.1" min="0.1" name="projectile_hitbox_radius" value="<?= htmlspecialchars((string) ($settings['projectile_hitbox_radius'] ?? '0.6'), ENT_QUOTES, 'UTF-8') ?>" required>
            </label>
            <label>
                <span>Mostrar linha de hitbox</span>
                <input type="checkbox" name="show_hitbox" value="1" <?= (($settings['show_hitbox'] ?? '1') === '1') ? 'checked' : '' ?>>
            </label>
            <button type="submit" name="save_settings" value="1">Salvar</button>
        </form>
    </div>

    <div class="panel">
        <h2>Administradores</h2>
        <div class="stack">
            <?php foreach ($users as $target): ?>
                <form method="post" class="room-card">
                    <div>
                        <strong><?= htmlspecialchars((string) $target['username'], ENT_QUOTES, 'UTF-8') ?></strong>
                        <div class="muted"><?= htmlspecialchars((string) $target['email'], ENT_QUOTES, 'UTF-8') ?></div>
                    </div>
                    <div class="row">
                        <input type="hidden" name="target_user_id" value="<?= (int) $target['user_id'] ?>">
                        <input type="hidden" name="make_admin" value="<?= (int) $target['is_admin'] === 1 ? 0 : 1 ?>">
                        <button type="submit" name="toggle_admin" value="1">
                            <?= (int) $target['is_admin'] === 1 ? 'Remover admin' : 'Tornar admin' ?>
                        </button>
                    </div>
                </form>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php render_footer(); ?>
