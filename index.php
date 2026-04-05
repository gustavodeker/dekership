<?php
$page = $_GET['page'] ?? 'login';

switch ($page) {
    case 'auth':
        include 'config/auth.php';
        break;
    case 'login':
        include 'web/login/login.php';
        break;
    case 'cadastro':
        include 'web/cadastro/cadastro.php';
        break;
    case 'lobby':
        include 'web/lobby/lobby.php';
        break;
    case 'game':
        include 'web/game/game.php';
        break;
    case 'profile':
        include 'web/profile/profile.php';
        break;
    case 'ranking':
        include 'web/ranking/ranking.php';
        break;
    case 'logout':
        include 'logout.php';
        break;
    default:
        include 'web/404/404.php';
        break;
}