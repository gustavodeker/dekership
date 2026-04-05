<?php

declare(strict_types=1);

$user = require_auth();
render_header('Game');
?>
<section class="panel">
    <div class="row between">
        <h1>Partida</h1>
        <div id="game-status">Aguardando sincronização</div>
    </div>
    <div class="hud">
        <div>Você: <strong id="score-self">0</strong></div>
        <div>Oponente: <strong id="score-opponent">0</strong></div>
    </div>
    <canvas id="game-canvas" width="900" height="540"></canvas>
</section>
<script>
window.DK_SESSION = <?= json_encode([
    'user' => $user,
    'sessionEndpoint' => '/web/api/session.php',
], JSON_UNESCAPED_SLASHES) ?>;
</script>
<script src="/web/game/game.js"></script>
<?php render_footer(); ?>
