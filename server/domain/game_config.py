from __future__ import annotations

import time

from server.config import settings
from server.db import fetch_all, get_pool


class GameConfigService:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self._loaded_at: float = 0.0
        self.ttl_seconds = 1.0

    async def ensure_schema(self) -> None:
        pool = get_pool()
        async with pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS game_settings (
                      setting_key VARCHAR(80) PRIMARY KEY,
                      setting_value VARCHAR(80) NOT NULL,
                      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS game_admin (
                      user_id INT(11) PRIMARY KEY,
                      granted_by_user_id INT(11) NULL,
                      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                      CONSTRAINT fk_game_admin_user FOREIGN KEY (user_id) REFERENCES usuario(id),
                      CONSTRAINT fk_game_admin_granted_by FOREIGN KEY (granted_by_user_id) REFERENCES usuario(id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                await cursor.execute(
                    """
                    INSERT INTO game_settings (setting_key, setting_value)
                    VALUES
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
                    ON DUPLICATE KEY UPDATE setting_value = setting_value
                    """
                )
                await cursor.execute(
                    f"""
                    INSERT INTO game_admin (user_id, granted_by_user_id)
                    SELECT {settings.auth_id_column}, NULL
                    FROM {settings.auth_user_table}
                    WHERE {settings.auth_username_column} = %s
                    ON DUPLICATE KEY UPDATE user_id = user_id
                    """,
                    (settings.default_admin_username,),
                )
                await connection.commit()

    async def get_settings(self, mode: str = "1v1") -> dict[str, float]:
        now = time.time()
        if now - self._loaded_at > self.ttl_seconds:
            rows = await fetch_all("SELECT setting_key, setting_value FROM game_settings")
            self._cache = {str(row["setting_key"]): str(row["setting_value"]) for row in rows}
            self._loaded_at = now

        prefix = "open_world_" if mode == "open_world" else "1v1_"

        def read_setting(key: str, default: str) -> str:
            prefixed_key = f"{prefix}{key}"
            if prefixed_key in self._cache:
                return self._cache[prefixed_key]
            return self._cache.get(key, default)

        return {
            "projectile_speed": float(read_setting("projectile_speed", "1.6")),
            "movement_speed": float(read_setting("movement_speed", "3.0")),
            "hits_to_win": max(1, int(float(read_setting("hits_to_win", "3")))),
            "fire_cooldown_ticks": max(1, int(float(read_setting("fire_cooldown_ticks", "6")))),
            "attack_range": max(0.1, float(read_setting("attack_range", "22"))),
            "mine_cooldown_ticks": max(1, int(float(read_setting("mine_cooldown_ticks", "100")))),
            "mine_max_active_per_player": max(1, int(float(read_setting("mine_max_active_per_player", "3")))),
            "render_smoothing": float(read_setting("render_smoothing", "0.25")),
            "player_hitbox_radius": float(read_setting("player_hitbox_radius", "5.4")),
            "projectile_hitbox_radius": float(read_setting("projectile_hitbox_radius", "0.6")),
            "mine_hitbox_radius": float(read_setting("mine_hitbox_radius", "2.4")),
            "mine_hits_to_destroy": max(1, int(float(read_setting("mine_hits_to_destroy", "2")))),
            "shield_points": max(0, int(float(read_setting("shield_points", "2")))),
            "shield_regen_seconds": max(1, int(float(read_setting("shield_regen_seconds", "10")))),
            "respawn_invulnerability_seconds": max(1, int(float(read_setting("respawn_invulnerability_seconds", "2")))),
            "monster_max_alive": max(0, int(float(read_setting("monster_max_alive", "8")))),
            "monster_life": max(1, int(float(read_setting("monster_life", "6")))),
            "monster_name": read_setting("monster_name", "-=[ Lordakia ]=-"),
            "monster_move_speed": max(0.1, float(read_setting("monster_move_speed", "1.2"))),
            "monster_hitbox_radius": max(0.1, float(read_setting("monster_hitbox_radius", "5.4"))),
            "monster_detection_radius": max(0.1, float(read_setting("monster_detection_radius", "26"))),
            "monster_attack_radius": max(0.1, float(read_setting("monster_attack_radius", "16"))),
            "monster_target_priority": read_setting("monster_target_priority", "attack_order"),
            "monster_projectile_speed": max(0.1, float(read_setting("monster_projectile_speed", "1.1"))),
            "monster_fire_cooldown_ticks": max(1, int(float(read_setting("monster_fire_cooldown_ticks", "35")))),
            "monster_respawn_seconds": max(1, int(float(read_setting("monster_respawn_seconds", "5")))),
            "show_monster_ranges": read_setting("show_monster_ranges", "0") != "0",
        }
