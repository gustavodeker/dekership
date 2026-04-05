import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..auth import validate_php_session_token
from ..config import settings
from ..domain.matches import MatchService
from ..domain.ranking import RankingService
from ..domain.rooms import RoomService
from .connection_manager import ConnectionManager

router = APIRouter()

room_service = RoomService()
ranking_service = RankingService()
manager = ConnectionManager()


async def _send_to_user(user_id: int, envelope: dict[str, Any]) -> None:
    ws = manager.get_websocket_by_user(user_id)
    if ws is None:
        return
    try:
        await ws.send_json(envelope)
    except Exception:
        manager.disconnect(ws)


async def _broadcast(user_ids: list[int], envelope: dict[str, Any]) -> None:
    for user_id in user_ids:
        await _send_to_user(user_id, envelope)


match_service = MatchService(
    ranking_service=ranking_service,
    tick_rate=settings.ws_tick_rate,
    reconnect_timeout_seconds=settings.reconnect_timeout_seconds,
    send_to_user=_send_to_user,
    broadcast=_broadcast,
)


def _err(code: str, message: str) -> dict[str, Any]:
    return {"event": "error", "payload": {"code": code, "message": message}}


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    ctx = None
    try:
        while True:
            try:
                raw = await websocket.receive_text()
            except (WebSocketDisconnect, RuntimeError):
                break
            try:
                envelope = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(_err("INVALID_PAYLOAD", "JSON invalido"))
                continue

            event = envelope.get("event")
            payload = envelope.get("payload") or {}

            if event == "auth":
                token = str(payload.get("token") or "")
                if not token:
                    print("[ws auth] token ausente")
                    await websocket.send_json(_err("UNAUTHORIZED", "token ausente"))
                    continue
                auth_user = await validate_php_session_token(token)
                if auth_user is None:
                    print(f"[ws auth] token invalido prefix={token[:10]}")
                    await websocket.send_json(_err("UNAUTHORIZED", "token invalido"))
                    continue
                print(f"[ws auth] ok user_id={auth_user.user_id} user={auth_user.username} token_prefix={token[:10]}")

                manager.register_identity(websocket, auth_user.user_id, auth_user.username)
                room = await room_service.find_room_by_player(auth_user.user_id)
                if room:
                    match = match_service.get_match_by_room(room.room_id)
                    if match:
                        await match_service.mark_reconnected(match, auth_user.user_id)

                await websocket.send_json(
                    {
                        "event": "auth_ok",
                        "payload": {"user_id": auth_user.user_id, "username": auth_user.username},
                    }
                )
                continue

            ctx = manager.get_ctx(websocket)
            if not ctx or ctx.user_id is None or ctx.username is None:
                await websocket.send_json(_err("UNAUTHORIZED", "auth obrigatorio"))
                continue

            if event == "room_create":
                room_name = str(payload.get("room_name") or "Sala")[:80]
                room = await room_service.create_room(room_name, ctx.user_id)
                player = await room_service.join_room(room, ctx.user_id, ctx.username)
                print(f"[room_create] room={room.room_id} by={ctx.user_id}")
                await websocket.send_json(
                    {
                        "event": "room_created",
                        "payload": {"room_id": room.room_id, "status": room.status},
                    }
                )
                await websocket.send_json(
                    {
                        "event": "room_joined",
                        "payload": {"room_id": room.room_id, "side": player.side, "players": len(room.players)},
                    }
                )
                continue

            if event == "room_list":
                rooms = await room_service.list_open_rooms()
                await websocket.send_json(
                    {
                        "event": "room_list_result",
                        "payload": {
                            "rooms": [
                                {
                                    "room_id": r.room_id,
                                    "name": r.name,
                                    "players": len(r.players),
                                }
                                for r in rooms
                            ]
                        },
                    }
                )
                continue

            if event == "room_join":
                room_id = str(payload.get("room_id") or "")
                room = await room_service.get_room(room_id)
                if room is None:
                    await websocket.send_json(_err("INVALID_STATE", "sala nao encontrada"))
                    continue
                try:
                    player = await room_service.join_room(room, ctx.user_id, ctx.username)
                    print(f"[room_join] room={room.room_id} user={ctx.user_id} players={len(room.players)} status={room.status}")
                except ValueError as exc:
                    await websocket.send_json(_err(str(exc), "falha ao entrar"))
                    continue

                await websocket.send_json(
                    {
                        "event": "room_joined",
                        "payload": {"room_id": room.room_id, "side": player.side, "players": len(room.players)},
                    }
                )

                if room.status == "playing":
                    match = match_service.get_match_by_room(room.room_id)
                    if match:
                        await websocket.send_json(
                            {
                                "event": "match_start",
                                "payload": match_service.get_match_payload(match),
                            }
                        )
                    continue

                if len(room.players) == 2:
                    await room_service.set_room_playing(room)
                    match = await match_service.maybe_start_match(room)
                    if match:
                        print(f"[match_start] match={match.match_id} room={room.room_id}")
                continue

            if event == "player_input":
                if not manager.allow_input(websocket, settings.input_rate_limit_per_second):
                    await websocket.send_json(_err("RATE_LIMIT", "maximo de inputs por segundo excedido"))
                    continue

                room = await room_service.find_room_by_player(ctx.user_id)
                if room is None:
                    await websocket.send_json(_err("INVALID_STATE", "usuario sem sala"))
                    continue

                match = match_service.get_match_by_room(room.room_id)
                if match is None:
                    await websocket.send_json(_err("INVALID_STATE", "partida nao iniciada"))
                    continue

                seq = int(payload.get("seq", 0))
                move_x = int(payload.get("move_x", 0))
                shoot = bool(payload.get("shoot", False))
                await match_service.submit_input(match, ctx.user_id, seq, move_x, shoot)
                continue

            if event == "ping":
                await websocket.send_json({"event": "pong", "payload": {"ts": payload.get("ts")}})
                continue

            await websocket.send_json(_err("INVALID_STATE", "evento nao suportado"))
    finally:
        ctx = manager.disconnect(websocket)
        if ctx and ctx.user_id is not None:
            room = await room_service.find_room_by_player(ctx.user_id)
            if room:
                match = match_service.get_match_by_room(room.room_id)
                if match:
                    await match_service.mark_disconnected(match, ctx.user_id)
