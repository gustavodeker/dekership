<?php

declare(strict_types=1);

$user = require_admin();
ensure_admin_schema();

$success = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
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
        <h1>Configuracoes</h1>
        <?php if ($success !== null): ?>
            <div class="success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
        <?php endif; ?>
        <?php if ($error !== null): ?>
            <div class="alert"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
        <?php endif; ?>
        <div class="stack">
            <a class="room-card" href="/index.php?page=settings_1v1">
                <div>
                    <strong>Config 1v1</strong>
                    <div class="muted">Parametros exclusivos do modo 1v1</div>
                </div>
            </a>
            <a class="room-card" href="/index.php?page=settings_openworld">
                <div>
                    <strong>Config Mundo Aberto</strong>
                    <div class="muted">Parametros exclusivos do modo continuo</div>
                </div>
            </a>
        </div>
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
