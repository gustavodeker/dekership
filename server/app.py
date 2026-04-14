from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from server.auth import get_user_by_token
from server.config import settings
from server.db import close_pool, open_pool
from server.domain.game_config import GameConfigService
from server.domain.matches import MatchRegistry
from server.domain.open_world import OpenWorldService
from server.domain.ranking import get_profile, get_ranking
from server.domain.rooms import RoomRegistry
from server.domain.simulation import SimulationService
from server.ws.connection_manager import ConnectionManager
from server.ws.router import build_ws_router


app = FastAPI(title="Dekership 1v1")
room_registry = RoomRegistry()
match_registry = MatchRegistry()
connection_manager = ConnectionManager()
game_config_service = GameConfigService()
simulation_service = SimulationService(room_registry, match_registry, connection_manager, game_config_service)
open_world_service = OpenWorldService(connection_manager, game_config_service, max_players=50)
app.include_router(
    build_ws_router(
        room_registry,
        match_registry,
        simulation_service,
        open_world_service,
        connection_manager,
        settings.input_rate_limit_per_second,
    )
)


@app.on_event("startup")
async def startup_event() -> None:
    await open_pool()
    await game_config_service.ensure_schema()
    await open_world_service.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await open_world_service.stop()
    await close_pool()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rooms")
async def rooms() -> dict[str, list[dict]]:
    return {"rooms": await room_registry.list_rooms()}


@app.get("/ranking")
async def ranking() -> dict[str, list[dict]]:
    return {"items": await get_ranking()}


@app.get("/profile")
async def profile(token: Annotated[str, Query(min_length=1)]) -> dict:
    user = await get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="token invalido")
    profile_data = await get_profile(user.user_id)
    if profile_data is None:
        return {
            "user_id": user.user_id,
            "username": user.username,
            "wins": 0,
            "losses": 0,
            "disconnects": 0,
        }
    return profile_data
