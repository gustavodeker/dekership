from dataclasses import dataclass

from .db import get_conn


@dataclass(frozen=True)
class AuthUser:
    user_id: int
    username: str


async def validate_php_session_token(token: str) -> AuthUser | None:
    token = token.strip()
    if not token:
        return None
    query = "SELECT id, usuario FROM usuario WHERE token = %s LIMIT 1"
    async with get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (token,))
            row = await cur.fetchone()
    if not row:
        return None
    return AuthUser(user_id=int(row[0]), username=str(row[1]))
