<?php

declare(strict_types=1);

$user = require_auth();
render_header('Game');
?>
<section class="panel game-panel">
    <canvas id="game-canvas" width="1366" height="768"></canvas>
</section>
<script>
window.DK_SESSION = <?= json_encode([
    'user' => $user,
    'sessionEndpoint' => '/web/api/session.php',
], JSON_UNESCAPED_SLASHES) ?>;
</script>
<script src="/web/game/game.js"></script>
<?php render_footer(); ?>

