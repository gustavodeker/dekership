from __future__ import annotations

from server.config import settings
from server.db import fetch_all, fetch_one


async def get_ranking(limit: int = 100) -> list[dict]:
    query = f"""
        SELECT
            u.{settings.auth_display_column} AS username,
            s.user_id,
            s.wins,
            s.losses,
            s.disconnects
        FROM player_stats s
        JOIN {settings.auth_user_table} u ON u.{settings.auth_id_column} = s.user_id
        ORDER BY s.wins DESC, s.losses ASC
        LIMIT %s
    """
    return await fetch_all(query, (limit,))


async def get_profile(user_id: int) -> dict | None:
    query = f"""
        SELECT
            u.{settings.auth_display_column} AS username,
            s.user_id,
            s.wins,
            s.losses,
            s.disconnects
        FROM player_stats s
        JOIN {settings.auth_user_table} u ON u.{settings.auth_id_column} = s.user_id
        WHERE s.user_id = %s
        LIMIT 1
    """
    return await fetch_one(query, (user_id,))
