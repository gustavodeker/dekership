<?php
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');

require_once __DIR__ . '/../../config/auth.php';
sessionVerif();

global $usuario;
$sessionToken = $_SESSION['TOKEN'] ?? '';
$sessionUser = auth($sessionToken);
echo json_encode([
    'ok' => true,
    'token' => $sessionToken,
    'username' => $usuario['usuario'] ?? '',
    'user_id' => (int)($usuario['id'] ?? 0),
    'token_prefix' => substr($sessionToken, 0, 10),
    'token_valid_php' => $sessionUser ? true : false,
    'db_host_php' => getenv('DB_HOST') ?: '',
    'db_name_php' => getenv('DB_NAME') ?: '',
]);
