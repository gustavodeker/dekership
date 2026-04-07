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
                      ('projectile_speed', '1.6'),
                      ('movement_speed', '3.0'),
                      ('hits_to_win', '3'),
                      ('fire_cooldown_ticks', '6'),
                      ('mine_cooldown_ticks', '100'),
                      ('ws_mode', 'vps'),
                      ('render_smoothing', '0.25'),
                      ('player_hitbox_radius', '5.4'),
                      ('projectile_hitbox_radius', '0.6'),
                      ('mine_hitbox_radius', '2.4'),
                      ('mine_hits_to_destroy', '2'),
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

    async def get_settings(self) -> dict[str, float]:
        now = time.time()
        if now - self._loaded_at > self.ttl_seconds:
            rows = await fetch_all("SELECT setting_key, setting_value FROM game_settings")
            self._cache = {str(row["setting_key"]): str(row["setting_value"]) for row in rows}
            self._loaded_at = now
        return {
            "projectile_speed": float(self._cache.get("projectile_speed", "1.6")),
            "movement_speed": float(self._cache.get("movement_speed", "3.0")),
            "hits_to_win": max(1, int(float(self._cache.get("hits_to_win", "3")))),
            "fire_cooldown_ticks": max(1, int(float(self._cache.get("fire_cooldown_ticks", "6")))),
            "mine_cooldown_ticks": max(1, int(float(self._cache.get("mine_cooldown_ticks", "100")))),
            "render_smoothing": float(self._cache.get("render_smoothing", "0.25")),
            "player_hitbox_radius": float(self._cache.get("player_hitbox_radius", "5.4")),
            "projectile_hitbox_radius": float(self._cache.get("projectile_hitbox_radius", "0.6")),
            "mine_hitbox_radius": float(self._cache.get("mine_hitbox_radius", "2.4")),
            "mine_hits_to_destroy": max(1, int(float(self._cache.get("mine_hits_to_destroy", "2")))),
        }
