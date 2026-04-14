<?php

declare(strict_types=1);

require __DIR__ . '/web/bootstrap.php';

$page = $_GET['page'] ?? 'login';
$routes = [
    'login' => __DIR__ . '/web/login.php',
    'cadastro' => __DIR__ . '/web/cadastro.php',
    'lobby' => __DIR__ . '/web/lobby/lobby.php',
    'game' => __DIR__ . '/web/game/game.php',
    'openworld' => __DIR__ . '/web/game/openworld.php',
    'profile' => __DIR__ . '/web/profile/profile.php',
    'ranking' => __DIR__ . '/web/ranking/ranking.php',
    'settings' => __DIR__ . '/web/settings.php',
    'settings_1v1' => __DIR__ . '/web/settings_1v1.php',
    'settings_openworld' => __DIR__ . '/web/settings_openworld.php',
];

if (!isset($routes[$page])) {
    http_response_code(404);
    exit('Page not found');
}

require $routes[$page];
