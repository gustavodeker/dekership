<?php
include 'config/auth.php';
sessionVerif();
$token = $_SESSION['TOKEN'];
$wsUrl = wsUrl();
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dekership - Game 1v1</title>
    <link rel="stylesheet" href="web/assets/tailwind.css">
    <link rel="stylesheet" href="web/game/game.css">
</head>
<body>
<?php include 'header.php'; ?>
<div class="container">
    <div class="card">
        <div class="row" style="justify-content: space-between;">
            <h2 style="margin: 0;">Partida 1v1</h2>
            <button id="leaveBtn" class="btn btn-danger" type="button">Voltar ao lobby</button>
        </div>
        <p id="statusText">Conectando...</p>
        <div class="row" style="gap: 24px;">
            <div>Você: <strong id="myScore">0</strong></div>
            <div>Oponente: <strong id="enemyScore">0</strong></div>
        </div>
        <canvas id="gameCanvas" width="900" height="420"></canvas>
    </div>
</div>
<script>
window.DEKERSHIP_GAME_CFG = {
    token: <?= json_encode($token) ?>,
    wsUrl: <?= json_encode($wsUrl) ?>,
    roomId: localStorage.getItem('dk_room_id') || '',
    matchId: localStorage.getItem('dk_match_id') || ''
};
</script>
<script src="web/game/game.js"></script>
</body>
</html>