from __future__ import annotations

from typing import Any

import aiomysql

from server.config import settings

pool: aiomysql.Pool | None = None


async def open_pool() -> None:
    global pool
    if pool is not None:
        return
    pool = await aiomysql.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_pass,
        db=settings.db_name,
        minsize=1,
        maxsize=10,
        autocommit=True,
        charset="utf8mb4",
    )


async def close_pool() -> None:
    global pool
    if pool is None:
        return
    pool.close()
    await pool.wait_closed()
    pool = None


def get_pool() -> aiomysql.Pool:
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool


async def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    async with get_pool().acquire() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchone()


async def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    async with get_pool().acquire() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params)
            return list(await cursor.fetchall())
