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

            if ($projectileSpeed <= 0 || $movementSpeed <= 0) {
                throw new RuntimeException('Valores invalidos');
            }

            $stmt = db()->prepare(
                'INSERT INTO game_settings (setting_key, setting_value)
                 VALUES (:setting_key, :setting_value)
                 ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)'
            );
            $stmt->execute(['setting_key' => 'projectile_speed', 'setting_value' => (string) $projectileSpeed]);
            $stmt->execute(['setting_key' => 'movement_speed', 'setting_value' => (string) $movementSpeed]);
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
