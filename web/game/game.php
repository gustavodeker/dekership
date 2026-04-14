<?php

declare(strict_types=1);

$user = require_auth();
render_header('Game');
?>
<section class="panel game-panel">
    <canvas id="game-canvas" width="1366" height="768"></canvas>
    <div id="game-start-overlay" class="game-start-overlay" aria-live="polite" hidden></div>
    <div id="shield-regen-box" class="shield-regen-box" aria-live="polite">
        <div class="shield-regen-box__label">ESCUDO</div>
        <div id="shield-regen-value" class="shield-regen-box__value">READY</div>
    </div>
    <div id="mine-cooldown-box" class="mine-cooldown-box" aria-live="polite">
        <div class="mine-cooldown-box__label">MINA (1)</div>
        <div id="mine-cooldown-value" class="mine-cooldown-box__value">0.0s</div>
    </div>
</section>
<script>
window.DK_SESSION = <?= json_encode([
    'user' => $user,
    'sessionEndpoint' => '/web/api/session.php',
], JSON_UNESCAPED_SLASHES) ?>;
</script>
<script src="/web/game/game.js"></script>
<?php render_footer(); ?>

