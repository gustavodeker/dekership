<?php

declare(strict_types=1);

$config = app_config();
require_auth();
$sql = sprintf(
    'SELECT u.%s AS username, s.wins, s.losses, s.disconnects
     FROM player_stats s
     JOIN %s u ON u.%s = s.user_id
     ORDER BY s.wins DESC, s.losses ASC
     LIMIT 100',
    $config['auth_display_column'],
    $config['auth_user_table'],
    $config['auth_id_column']
);
$items = db()->query($sql)->fetchAll();

render_header('Ranking');
?>
<section class="panel">
    <h1>Ranking</h1>
    <table class="table">
        <thead>
            <tr>
                <th>Usuário</th>
                <th>Vitórias</th>
                <th>Derrotas</th>
                <th>Desconexões</th>
            </tr>
        </thead>
        <tbody>
            <?php foreach ($items as $item): ?>
                <tr>
                    <td><?= htmlspecialchars((string) $item['username'], ENT_QUOTES, 'UTF-8') ?></td>
                    <td><?= (int) $item['wins'] ?></td>
                    <td><?= (int) $item['losses'] ?></td>
                    <td><?= (int) $item['disconnects'] ?></td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>
</section>
<?php render_footer(); ?>
