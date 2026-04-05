from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from .auth import validate_php_session_token
from .config import settings
from .db import close_pool, init_pool
from .domain.ranking import RankingService
from .ws.router import room_service, router

ranking_service = RankingService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Dekership WS Server", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "db_host": settings.db_host, "db_name": settings.db_name}


@app.get("/rooms")
async def rooms() -> dict[str, list[dict[str, int | str]]]:
    open_rooms = await room_service.list_open_rooms()
    return {
        "rooms": [
            {
                "room_id": room.room_id,
                "name": room.name,
                "players": len(room.players),
                "status": room.status,
            }
            for room in open_rooms
        ]
    }


@app.get("/ranking")
async def ranking(limit: int = Query(default=100, ge=1, le=200)) -> dict[str, list[dict[str, int | str]]]:
    return {"items": await ranking_service.get_top_ranking(limit=limit)}


@app.get("/profile")
async def profile(token: str) -> dict[str, int | str]:
    auth_user = await validate_php_session_token(token)
    if auth_user is None:
        raise HTTPException(status_code=401, detail="token invalido")

    stats = await ranking_service.get_user_stats(auth_user.user_id)
    if stats is None:
        stats = {"wins": 0, "losses": 0, "disconnects": 0}

    return {
        "user_id": auth_user.user_id,
        "username": auth_user.username,
        **stats,
    }
