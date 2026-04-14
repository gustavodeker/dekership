<?php

declare(strict_types=1);

$user = require_auth();
render_header('Mundo Aberto');
?>
<section class="panel game-panel">
    <canvas id="open-world-canvas" width="1366" height="768"></canvas>
    <div id="open-world-status-box" class="open-world-status-box">
        <div id="open-world-status">Conectando...</div>
        <div id="open-world-stats">Players: 0/50 | K: 0 | D: 0</div>
    </div>
    <div id="open-world-death-overlay" class="open-world-death-overlay" hidden>
        <div id="open-world-death-message" class="open-world-death-overlay__message">Você morreu</div>
        <div id="open-world-death-countdown" class="open-world-death-overlay__countdown">Renascer em 3s</div>
        <button id="open-world-respawn-btn" type="button" hidden>Renascer</button>
    </div>
    <div id="shield-regen-box" class="shield-regen-box" aria-live="polite">
        <div class="shield-regen-box__label">ESCUDO</div>
        <div id="shield-regen-value" class="shield-regen-box__value">READY</div>
    </div>
    <div id="mine-cooldown-box" class="mine-cooldown-box" aria-live="polite">
        <div class="mine-cooldown-box__label">MINA (1)</div>
        <div id="mine-cooldown-value" class="mine-cooldown-box__value">READY</div>
    </div>
</section>
<script>
window.DK_SESSION = <?= json_encode([
    'user' => $user,
    'sessionEndpoint' => '/web/api/session.php',
    'gameMode' => 'open_world',
], JSON_UNESCAPED_SLASHES) ?>;
</script>
<script src="/web/game/openworld.js"></script>
<?php render_footer(); ?>
