<?php
include 'config/auth.php';
sessionVerif();
global $usuario;
$stats = userStats((int)$usuario['id']);
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dekership - Perfil</title>
    <link rel="stylesheet" href="web/assets/tailwind.css">
    <link rel="stylesheet" href="web/profile/profile.css">
</head>
<body>
<?php include 'header.php'; ?>
<div class="container">
    <div class="card">
        <h2>Perfil</h2>
        <p>Usuário: <strong><?= htmlspecialchars($usuario['usuario']) ?></strong></p>
        <div class="row stats">
            <div class="stat"><span>Vitórias</span><strong><?= (int)$stats['wins'] ?></strong></div>
            <div class="stat"><span>Derrotas</span><strong><?= (int)$stats['losses'] ?></strong></div>
            <div class="stat"><span>Desconexões</span><strong><?= (int)$stats['disconnects'] ?></strong></div>
        </div>
    </div>
</div>
</body>
</html>