<?php
include_once 'config/auth.php';
$logged = isset($_SESSION['TOKEN']);
?>
<link rel="stylesheet" href="css/header.css">
<nav class="menu">
    <ul>
        <?php if ($logged): ?>
            <a href="index.php?page=lobby">Lobby</a>
            <a href="index.php?page=game">Game</a>
            <a href="index.php?page=profile">Perfil</a>
            <a href="index.php?page=ranking">Ranking</a>
            <a href="logout.php">Sair</a>
        <?php else: ?>
            <a href="index.php?page=login">Login</a>
            <a href="index.php?page=cadastro">Cadastro</a>
        <?php endif; ?>
    </ul>
</nav>