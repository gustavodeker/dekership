<?php declare(strict_types=1); ?>
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($title, ENT_QUOTES, 'UTF-8') ?></title>
    <link rel="stylesheet" href="/web/assets/app.css">
</head>
<body>
<div class="layout">
    <header class="topbar">
        <div class="brand">Dekership 1v1</div>
        <nav class="nav">
            <a href="/index.php?page=lobby">Lobby</a>
            <a href="/index.php?page=profile">Perfil</a>
            <a href="/index.php?page=ranking">Ranking</a>
            <?php if ($user !== null): ?>
                <?php if (is_admin_user((int) $user['user_id'])): ?>
                    <a href="/index.php?page=settings">Configuracoes</a>
                <?php endif; ?>
                <span><?= htmlspecialchars((string) $user['display_name'], ENT_QUOTES, 'UTF-8') ?></span>
                <a href="/web/api/logout.php">Sair</a>
            <?php endif; ?>
        </nav>
    </header>
    <main class="content">
