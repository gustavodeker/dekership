from __future__ import annotations

from dataclasses import dataclass

from server.config import settings
from server.db import fetch_one


@dataclass(slots=True, frozen=True)
class AuthUser:
    user_id: int
    username: str


async def get_user_by_token(token: str) -> AuthUser | None:
    query = f"""
        SELECT
            {settings.auth_id_column} AS user_id,
            {settings.auth_display_column} AS username
        FROM {settings.auth_user_table}
        WHERE {settings.auth_token_column} = %s
        LIMIT 1
    """
    row = await fetch_one(query, (token,))
    if row is None:
        return None
    return AuthUser(user_id=int(row["user_id"]), username=str(row["username"]))
