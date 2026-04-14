from __future__ import annotations

import time
from collections import deque

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from server.auth import AuthUser, get_user_by_token
from server.config import settings
from server.domain.matches import MatchRegistry
from server.domain.open_world import OpenWorldService
from server.domain.rooms import RoomRegistry, persist_room_closed, persist_room_created, persist_room_started
from server.domain.simulation import SimulationService
from server.models import AuthPayload, Envelope, PlayerInputPayload, RoomCreatePayload, RoomJoinPayload
from server.ws.connection_manager import ConnectionManager


class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.entries: dict[int, deque[float]] = {}

    def allow(self, key: int) -> bool:
        now = time.time()
        bucket = self.entries.setdefault(key, deque())
        while bucket and now - bucket[0] > 1:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True


def build_ws_router(
    rooms: RoomRegistry,
    matches: MatchRegistry,
    simulation: SimulationService,
    open_world: OpenWorldService,
    manager: ConnectionManager,
    input_rate_limit: int,
) -> APIRouter:
    router = APIRouter()
    limiter = RateLimiter(input_rate_limit)

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        authed_user: AuthUser | None = None
        try:
            while True:
                raw = await websocket.receive_json()
                envelope = Envelope.model_validate(raw)

                if envelope.event == "auth":
                    payload = AuthPayload.model_validate(envelope.payload)
                    authed_user = await get_user_by_token(payload.token)
                    if authed_user is None:
                        await manager.send_error(websocket, "UNAUTHORIZED", "token invalido")
                        continue
                    manager.bind_user(authed_user.user_id, websocket)
                    room = await rooms.attach_existing_connection(authed_user.user_id, websocket)
                    await manager.send_json(
                        websocket,
                        "auth_ok",
                        {"user_id": authed_user.user_id, "username": authed_user.username},
                    )
                    if room is not None:
                        player = room.players[authed_user.user_id]
                        await manager.send_json(
                            websocket,
                            "room_joined",
                            {"room_id": room.room_id, "side": player.side, "players": len(room.players)},
                        )
                        if room.status == "playing" and room.match_id is not None:
                            match = await matches.get_by_room(room.room_id)
                            if match is not None:
                                await manager.send_json(
                                    websocket,
                                    "match_start",
                                    {"match_id": match.match_id, "tick_rate": settings.ws_tick_rate},
                                )
                    await manager.send_json(websocket, "room_list_result", {"rooms": await rooms.list_rooms()})
                    continue

                if authed_user is None:
                    await manager.send_error(websocket, "UNAUTHORIZED", "autenticacao obrigatoria")
                    continue

                if envelope.event == "room_list":
                    await manager.send_json(websocket, "room_list_result", {"rooms": await rooms.list_rooms()})
                    continue

                if envelope.event == "room_create":
                    payload = RoomCreatePayload.model_validate(envelope.payload)
                    previous_room, previous_room_closed = await rooms.leave_room(authed_user.user_id)
                    if previous_room_closed and previous_room is not None:
                        await persist_room_closed(previous_room)
                        await manager.broadcast(
                            previous_room,
                            "room_closed",
                            {"room_id": previous_room.room_id, "reason": "owner_left"},
                        )
                    room = await rooms.create_room(authed_user.user_id, payload.room_name.strip())
                    await persist_room_created(room)
                    await rooms.join_room(room.room_id, authed_user.user_id, authed_user.username, websocket)
                    await manager.send_json(websocket, "room_created", {"room_id": room.room_id, "status": room.status})
                    await manager.send_json(websocket, "room_joined", {"room_id": room.room_id, "side": "bottom", "players": 1})
                    await manager.broadcast_room_list(await rooms.list_rooms())
                    continue

                if envelope.event == "room_join":
                    payload = RoomJoinPayload.model_validate(envelope.payload)
                    try:
                        room, player, is_new, closed_rooms = await rooms.join_room(
                            payload.room_id,
                            authed_user.user_id,
                            authed_user.username,
                            websocket,
                        )
                    except ValueError as exc:
                        await manager.send_error(websocket, str(exc), "falha ao entrar")
                        continue
                    for closed_room in closed_rooms:
                        await persist_room_closed(closed_room)
                        await manager.broadcast(
                            closed_room,
                            "room_closed",
                            {"room_id": closed_room.room_id, "reason": "owner_left"},
                        )
                    await manager.send_json(
                        websocket,
                        "room_joined",
                        {"room_id": room.room_id, "side": player.side, "players": len(room.players)},
                    )
                    if room.status == "playing" and room.match_id is not None:
                        match = await matches.get_by_room(room.room_id)
                        if match is not None:
                            await manager.send_json(
                                websocket,
                                "match_start",
                                {"match_id": match.match_id, "tick_rate": settings.ws_tick_rate},
                            )
                    if is_new and len(room.players) == 2:
                        await persist_room_started(room)
                        match = await matches.start_match(room, room.room_db_id)
                        await manager.broadcast(
                            room,
                            "match_start",
                            {"match_id": match.match_id, "tick_rate": settings.ws_tick_rate},
                        )
                        await simulation.start(match)
                    await manager.broadcast_room_list(await rooms.list_rooms())
                    continue

                if envelope.event == "room_leave":
                    room, room_closed = await rooms.leave_room(authed_user.user_id)
                    if room is None:
                        await manager.send_error(websocket, "INVALID_STATE", "jogador sem sala")
                        continue
                    if room_closed:
                        await persist_room_closed(room)
                        await manager.broadcast(
                            room,
                            "room_closed",
                            {"room_id": room.room_id, "reason": "owner_left"},
                        )
                    await manager.send_json(websocket, "room_left", {"room_id": room.room_id})
                    await manager.broadcast_room_list(await rooms.list_rooms())
                    continue

                if envelope.event == "open_world_join":
                    room = await rooms.get_room_for_user(authed_user.user_id)
                    if room is not None:
                        if room.status == "playing":
                            await manager.send_error(
                                websocket,
                                "INVALID_STATE",
                                "saia da partida 1v1 antes de entrar no mundo aberto",
                            )
                            continue
                        previous_room, previous_room_closed = await rooms.leave_room(authed_user.user_id)
                        if previous_room_closed and previous_room is not None:
                            await persist_room_closed(previous_room)
                            await manager.broadcast(
                                previous_room,
                                "room_closed",
                                {"room_id": previous_room.room_id, "reason": "owner_left"},
                            )
                        await manager.broadcast_room_list(await rooms.list_rooms())
                    try:
                        await open_world.join(authed_user.user_id, authed_user.username)
                    except ValueError as exc:
                        await manager.send_error(websocket, str(exc), "falha ao entrar no mundo aberto")
                        continue
                    await manager.send_json(
                        websocket,
                        "open_world_joined",
                        {"world_id": "global", "max_players": open_world.max_players, "tick_rate": settings.ws_tick_rate},
                    )
                    continue

                if envelope.event == "open_world_leave":
                    left = await open_world.leave(authed_user.user_id)
                    if not left:
                        await manager.send_error(websocket, "INVALID_STATE", "jogador fora do mundo aberto")
                        continue
                    await manager.send_json(websocket, "open_world_left", {"world_id": "global"})
                    continue

                if envelope.event == "open_world_respawn":
                    ok, reason = await open_world.respawn(authed_user.user_id)
                    if not ok:
                        await manager.send_error(websocket, reason, "falha ao renascer")
                    continue

                if envelope.event == "player_input":
                    payload = PlayerInputPayload.model_validate(envelope.payload)
                    if not limiter.allow(authed_user.user_id) and not payload.shoot and not payload.drop_mine:
                        continue
                    room = await rooms.get_room_for_user(authed_user.user_id)
                    if room is not None and authed_user.user_id in room.players:
                        player = room.players[authed_user.user_id]
                        if payload.seq <= player.input_seq:
                            continue
                        player.input_seq = payload.seq
                        player.move_x = payload.move_x
                        player.move_y = payload.move_y
                        player.aim_x = payload.aim_x
                        player.aim_y = payload.aim_y
                        if payload.shoot:
                            player.shoot_requested = True
                        if payload.drop_mine:
                            player.mine_requested = True
                        continue
                    if await open_world.has_player(authed_user.user_id):
                        await open_world.apply_input(
                            authed_user.user_id,
                            payload.seq,
                            payload.move_x,
                            payload.move_y,
                            payload.aim_x,
                            payload.aim_y,
                            payload.shoot,
                            payload.drop_mine,
                            payload.target_type,
                            payload.target_id,
                        )
                        continue
                    await manager.send_error(websocket, "INVALID_STATE", "jogador sem modo ativo")
                    continue

                if envelope.event == "drop_mine":
                    room = await rooms.get_room_for_user(authed_user.user_id)
                    if room is not None and authed_user.user_id in room.players:
                        player = room.players[authed_user.user_id]
                        player.mine_requested = True
                        continue
                    if await open_world.has_player(authed_user.user_id):
                        await open_world.request_mine_drop(authed_user.user_id)
                        continue
                    await manager.send_error(websocket, "INVALID_STATE", "jogador sem modo ativo")
                    continue

                if envelope.event == "ping":
                    await manager.send_json(websocket, "pong", envelope.payload)
                    continue

                await manager.send_error(websocket, "INVALID_STATE", "evento desconhecido")
        except WebSocketDisconnect:
            if authed_user is not None:
                manager.unbind_user(authed_user.user_id, websocket)
                room = await rooms.get_room_for_user(authed_user.user_id)
                if (
                    room is not None
                    and room.created_by_user_id == authed_user.user_id
                    and room.status == "waiting"
                ):
                    closed_room, room_closed = await rooms.leave_room(authed_user.user_id)
                    if room_closed and closed_room is not None:
                        await persist_room_closed(closed_room)
                        await manager.broadcast(
                            closed_room,
                            "room_closed",
                            {"room_id": closed_room.room_id, "reason": "owner_disconnected"},
                        )
                else:
                    await rooms.mark_disconnected(authed_user.user_id)
                await open_world.leave(authed_user.user_id)
                await manager.broadcast_room_list(await rooms.list_rooms())
        except ValidationError:
            await manager.send_error(websocket, "INVALID_STATE", "payload invalido")

    return router
