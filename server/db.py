from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiomysql

from .config import settings


_pool: aiomysql.Pool | None = None


async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_pass,
            db=settings.db_name,
            autocommit=False,
            minsize=1,
            maxsize=10,
        )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


@asynccontextmanager
async def get_conn() -> AsyncIterator[aiomysql.Connection]:
    if _pool is None:
        await init_pool()
    assert _pool is not None
    conn = await _pool.acquire()
    try:
        yield conn
    finally:
        _pool.release(conn)