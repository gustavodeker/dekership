<?php
// Verifique se um parâmetro 'page' está presente na URL
$page = isset($_GET['page']) ? $_GET['page'] : 'login';

// Use um switch para determinar a ação com base no valor de 'page'
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
    case 'game':
        include 'web/game/game.php';
        break;
    case 'ranking':
        include 'web/ranking/ranking.php';
        break;
    case 'logout':
        include 'web/logout.php';
        break;
    default:
        include 'web/404/404.php'; // Página não encontrada
        break;
}
