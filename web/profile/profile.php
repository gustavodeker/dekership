<?php

declare(strict_types=1);

$user = require_auth();
$query = db()->prepare('SELECT wins, losses, disconnects FROM player_stats WHERE user_id = :user_id LIMIT 1');
$query->execute(['user_id' => $user['user_id']]);
$stats = $query->fetch() ?: ['wins' => 0, 'losses' => 0, 'disconnects' => 0];

render_header('Perfil');
?>
<section class="panel narrow">
    <h1>Perfil</h1>
    <div class="stats">
        <div><span>Usuário</span><strong><?= htmlspecialchars((string) $user['display_name'], ENT_QUOTES, 'UTF-8') ?></strong></div>
        <div><span>Vitórias</span><strong><?= (int) $stats['wins'] ?></strong></div>
        <div><span>Derrotas</span><strong><?= (int) $stats['losses'] ?></strong></div>
        <div><span>Desconexões</span><strong><?= (int) $stats['disconnects'] ?></strong></div>
    </div>
</section>
<?php render_footer(); ?>
