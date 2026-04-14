<?php

declare(strict_types=1);

$user = require_auth();
render_header('Lobby');
?>
<section class="grid">
    <div class="panel">
        <h1>Lobby</h1>
        <form id="create-room-form" class="stack">
            <label>
                <span>Nova sala</span>
                <input type="text" id="room-name" maxlength="80" required>
            </label>
            <button type="submit">Criar sala</button>
            <button type="button" id="open-world-btn">Entrar no mundo aberto</button>
            <button type="button" id="leave-room-btn">Sair da sala</button>
        </form>
    </div>
    <div class="panel">
        <div class="row between">
            <h2>Salas abertas</h2>
            <span class="muted">Tempo real</span>
        </div>
        <div id="lobby-status" class="muted">Conectando...</div>
        <div id="room-list" class="stack"></div>
    </div>
</section>
<script>
window.DK_SESSION = <?= json_encode([
    'user' => $user,
    'sessionEndpoint' => '/web/api/session.php',
], JSON_UNESCAPED_SLASHES) ?>;
</script>
<script src="/web/lobby/lobby.js"></script>
<?php render_footer(); ?>
