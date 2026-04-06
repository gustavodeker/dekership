<?php

declare(strict_types=1);

function env_value(string $key, ?string $default = null): ?string
{
    static $vars = null;
    if ($vars === null) {
        $vars = [];
        $envPath = dirname(__DIR__) . DIRECTORY_SEPARATOR . '.env';
        if (is_file($envPath)) {
            foreach (file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
                if (str_starts_with(trim($line), '#') || !str_contains($line, '=')) {
                    continue;
                }
                [$envKey, $envValue] = explode('=', $line, 2);
                $vars[trim($envKey)] = trim($envValue);
            }
        }
    }

    return $_ENV[$key] ?? $_SERVER[$key] ?? $vars[$key] ?? $default;
}

function app_config(): array
{
    $wsUrlVps = env_value('WS_URL_VPS', env_value('WS_URL', 'wss://dekership.dataleave.com.br/ws'));
    $wsUrlLocal = env_value('WS_URL_LOCAL', 'ws://127.0.0.1:8000/ws');

    return [
        'db_host' => env_value('DB_HOST', '127.0.0.1'),
        'db_port' => (int) env_value('DB_PORT', '3306'),
        'db_name' => env_value('DB_NAME', 'dekership'),
        'db_user' => env_value('DB_USER', 'root'),
        'db_pass' => env_value('DB_PASS', ''),
        'ws_url' => $wsUrlVps,
        'ws_url_vps' => $wsUrlVps,
        'ws_url_local' => $wsUrlLocal,
        'auth_user_table' => env_value('AUTH_USER_TABLE', 'usuario'),
        'auth_id_column' => env_value('AUTH_ID_COLUMN', 'id'),
        'auth_username_column' => env_value('AUTH_USERNAME_COLUMN', 'usuario'),
        'auth_display_column' => env_value('AUTH_DISPLAY_COLUMN', 'usuario'),
        'auth_password_column' => env_value('AUTH_PASSWORD_COLUMN', 'senha'),
        'auth_token_column' => env_value('AUTH_TOKEN_COLUMN', 'token'),
        'default_admin_username' => env_value('DEFAULT_ADMIN_USERNAME', 'deker'),
    ];
}
