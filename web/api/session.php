<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

header('Content-Type: application/json; charset=utf-8');

$user = current_user();
if ($user === null) {
    http_response_code(401);
    echo json_encode(['ok' => false, 'message' => 'unauthorized']);
    exit;
}

echo json_encode([
    'ok' => true,
    'user_id' => $user['user_id'],
    'username' => $user['username'],
    'display_name' => $user['display_name'],
    'token' => $user['token'],
    'ws_url' => app_config()['ws_url'],
], JSON_UNESCAPED_SLASHES);
