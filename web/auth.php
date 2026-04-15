<?php

declare(strict_types=1);

function current_user(): ?array
{
    return $_SESSION['auth_user'] ?? null;
}

function require_auth(): array
{
    $user = current_user();
    if ($user === null) {
        redirect_to('login');
    }
    return $user;
}

function login_user(string $username, string $password): bool
{
    $config = app_config();
    $sql = sprintf(
        'SELECT %s AS user_id, %s AS username, %s AS display_name, %s AS password_hash
         FROM %s
         WHERE %s = :username
         LIMIT 1',
        $config['auth_id_column'],
        $config['auth_username_column'],
        $config['auth_display_column'],
        $config['auth_password_column'],
        $config['auth_user_table'],
        $config['auth_username_column']
    );

    $stmt = db()->prepare($sql);
    $stmt->execute(['username' => $username]);
    $user = $stmt->fetch();

    if (!$user || !password_verify($password, (string) $user['password_hash'])) {
        return false;
    }

    $token = bin2hex(random_bytes(24));
    $update = sprintf(
        'UPDATE %s SET %s = :token WHERE %s = :user_id',
        $config['auth_user_table'],
        $config['auth_token_column'],
        $config['auth_id_column']
    );
    db()->prepare($update)->execute([
        'token' => $token,
        'user_id' => $user['user_id'],
    ]);

    session_regenerate_id(true);
    $_SESSION['auth_user'] = [
        'user_id' => (int) $user['user_id'],
        'username' => $user['username'],
        'display_name' => $user['display_name'],
        'token' => $token,
    ];

    return true;
}

function register_user(string $username, string $email, string $password): bool
{
    $config = app_config();
    $sql = sprintf(
        'INSERT INTO %s (%s, email, %s, dataCadastro)
         VALUES (:username, :email, :password_hash, NOW())',
        $config['auth_user_table'],
        $config['auth_username_column'],
        $config['auth_password_column']
    );

    $stmt = db()->prepare($sql);
    return $stmt->execute([
        'username' => $username,
        'email' => $email,
        'password_hash' => password_hash($password, PASSWORD_ARGON2ID),
    ]);
}

function logout_user(): void
{
    $_SESSION = [];
    if (session_id() !== '') {
        if (ini_get('session.use_cookies')) {
            $params = session_get_cookie_params();
            setcookie(session_name(), '', time() - 42000, $params['path'], $params['domain'], $params['secure'], $params['httponly']);
        }
        session_destroy();
    }
}

function ensure_admin_schema(): void
{
    $config = app_config();
    db()->exec(
        "CREATE TABLE IF NOT EXISTS game_settings (
            setting_key VARCHAR(80) PRIMARY KEY,
            setting_value VARCHAR(80) NOT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    );
    db()->exec(
        "CREATE TABLE IF NOT EXISTS game_admin (
            user_id INT(11) PRIMARY KEY,
            granted_by_user_id INT(11) NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_game_admin_user FOREIGN KEY (user_id) REFERENCES usuario(id),
            CONSTRAINT fk_game_admin_granted_by FOREIGN KEY (granted_by_user_id) REFERENCES usuario(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    );
    db()->exec(
        "INSERT INTO game_settings (setting_key, setting_value) VALUES
        ('1v1_projectile_speed', '1.6'),
        ('1v1_movement_speed', '3.0'),
        ('1v1_hits_to_win', '3'),
        ('1v1_fire_cooldown_ticks', '6'),
        ('1v1_attack_range', '22'),
        ('1v1_mine_cooldown_ticks', '100'),
        ('1v1_mine_max_active_per_player', '3'),
        ('1v1_render_smoothing', '0.25'),
        ('1v1_player_hitbox_radius', '5.4'),
        ('1v1_projectile_hitbox_radius', '0.6'),
        ('1v1_mine_hitbox_radius', '2.4'),
        ('1v1_mine_hits_to_destroy', '2'),
        ('1v1_shield_points', '2'),
        ('1v1_shield_regen_seconds', '10'),
        ('1v1_respawn_invulnerability_seconds', '2'),
        ('1v1_show_hitbox', '1'),
        ('open_world_projectile_speed', '1.6'),
        ('open_world_movement_speed', '3.0'),
        ('open_world_hits_to_win', '3'),
        ('open_world_fire_cooldown_ticks', '6'),
        ('open_world_attack_range', '22'),
        ('open_world_mine_cooldown_ticks', '100'),
        ('open_world_mine_max_active_per_player', '3'),
        ('open_world_render_smoothing', '0.25'),
        ('open_world_player_hitbox_radius', '5.4'),
        ('open_world_projectile_hitbox_radius', '0.6'),
        ('open_world_mine_hitbox_radius', '2.4'),
        ('open_world_mine_hits_to_destroy', '2'),
        ('open_world_shield_points', '2'),
        ('open_world_shield_regen_seconds', '10'),
        ('open_world_respawn_invulnerability_seconds', '2'),
        ('open_world_monster_max_alive', '8'),
        ('open_world_monster_life', '6'),
        ('open_world_monster_name', '-=[ Lordakia ]=-'),
        ('open_world_monster_move_speed', '1.2'),
        ('open_world_monster_hitbox_radius', '5.4'),
        ('open_world_monster_detection_radius', '26'),
        ('open_world_monster_attack_radius', '16'),
        ('open_world_monster_target_priority', 'attack_order'),
        ('open_world_monster_projectile_speed', '1.1'),
        ('open_world_monster_fire_cooldown_ticks', '35'),
        ('open_world_monster_respawn_seconds', '5'),
        ('open_world_show_monster_ranges', '0'),
        ('open_world_show_hitbox', '1'),
        ('projectile_speed', '1.6'),
        ('movement_speed', '3.0'),
        ('hits_to_win', '3'),
        ('fire_cooldown_ticks', '6'),
        ('attack_range', '22'),
        ('mine_cooldown_ticks', '100'),
        ('mine_max_active_per_player', '3'),
        ('ws_mode', 'vps'),
        ('render_smoothing', '0.25'),
        ('player_hitbox_radius', '5.4'),
        ('projectile_hitbox_radius', '0.6'),
        ('mine_hitbox_radius', '2.4'),
        ('mine_hits_to_destroy', '2'),
        ('shield_points', '2'),
        ('shield_regen_seconds', '10'),
        ('respawn_invulnerability_seconds', '2'),
        ('monster_max_alive', '8'),
        ('monster_life', '6'),
        ('monster_name', '-=[ Lordakia ]=-'),
        ('monster_move_speed', '1.2'),
        ('monster_hitbox_radius', '5.4'),
        ('monster_detection_radius', '26'),
        ('monster_attack_radius', '16'),
        ('monster_target_priority', 'attack_order'),
        ('monster_projectile_speed', '1.1'),
        ('monster_fire_cooldown_ticks', '35'),
        ('monster_respawn_seconds', '5'),
        ('show_monster_ranges', '0'),
        ('show_hitbox', '1')
        ON DUPLICATE KEY UPDATE setting_value = setting_value"
    );

    $sql = sprintf(
        'INSERT INTO game_admin (user_id, granted_by_user_id)
         SELECT %s, NULL
         FROM %s
         WHERE %s = :username
         ON DUPLICATE KEY UPDATE user_id = user_id',
        $config['auth_id_column'],
        $config['auth_user_table'],
        $config['auth_username_column']
    );
    db()->prepare($sql)->execute(['username' => $config['default_admin_username']]);
}

function is_admin_user(int $userId): bool
{
    ensure_admin_schema();
    $stmt = db()->prepare('SELECT 1 FROM game_admin WHERE user_id = :user_id LIMIT 1');
    $stmt->execute(['user_id' => $userId]);
    return (bool) $stmt->fetchColumn();
}

function require_admin(): array
{
    $user = require_auth();
    if (!is_admin_user((int) $user['user_id'])) {
        http_response_code(403);
        exit('Forbidden');
    }
    return $user;
}
