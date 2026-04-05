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
    <title>Dekership - Lobby</title>
    <link rel="stylesheet" href="web/assets/tailwind.css">
    <link rel="stylesheet" href="web/lobby/lobby.css">
</head>
<body>
<?php include 'header.php'; ?>
<div class="container">
    <div class="card">
        <h2>Lobby 1v1</h2>
        <div class="row">
            <input id="roomName" class="input" type="text" maxlength="80" placeholder="Nome da sala">
            <button id="createRoomBtn" class="btn" type="button">Criar sala</button>
            <button id="refreshBtn" class="btn" type="button">Atualizar salas</button>
        </div>
        <p id="statusText">Conectando...</p>
    </div>

    <div class="card" style="margin-top: 12px;">
        <h3>Salas abertas</h3>
        <table class="table" id="roomsTable">
            <thead>
            <tr>
                <th>Sala</th>
                <th>Jogadores</th>
                <th>Ação</th>
            </tr>
            </thead>
            <tbody id="roomsBody"></tbody>
        </table>
    </div>
</div>
<script>
window.DEKERSHIP_CFG = {
    token: <?= json_encode($token) ?>,
    wsUrl: <?= json_encode($wsUrl) ?>
};
</script>
<script src="web/lobby/lobby.js"></script>
</body>
</html>