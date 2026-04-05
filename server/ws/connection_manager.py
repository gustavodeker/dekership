from __future__ import annotations

from typing import Any

from fastapi import WebSocket

from server.domain.matches import MatchState
from server.domain.rooms import RoomState
from server.ws.events import make_event


class ConnectionManager:
    def __init__(self) -> None:
        self.connections_by_user: dict[int, WebSocket] = {}

    def bind_user(self, user_id: int, websocket: WebSocket) -> None:
        self.connections_by_user[user_id] = websocket

    def unbind_user(self, user_id: int, websocket: WebSocket | None = None) -> None:
        current = self.connections_by_user.get(user_id)
        if current is None:
            return
        if websocket is not None and current is not websocket:
            return
        self.connections_by_user.pop(user_id, None)

    async def send_json(self, websocket: WebSocket | None, event: str, payload: dict[str, Any]) -> None:
        if websocket is None:
            return
        try:
            await websocket.send_json(make_event(event, payload))
        except Exception:
            return

    async def send_error(self, websocket: WebSocket, code: str, message: str) -> None:
        try:
            await websocket.send_json(make_event("error", {"code": code, "message": message}))
        except Exception:
            return

    async def broadcast(self, room: RoomState, event: str, payload: dict[str, Any]) -> None:
        for player in room.players.values():
            if player.connected and player.websocket is not None:
                try:
                    await player.websocket.send_json(make_event(event, payload))
                except Exception:
                    player.connected = False
                    player.websocket = None

    async def broadcast_state(self, room: RoomState, match: MatchState) -> None:
        players = {player.side: player for player in match.players.values()}
        await self.broadcast(
            room,
            "state",
            {
                "tick": match.tick,
                "p1": {
                    "user_id": players["bottom"].user_id,
                    "username": players["bottom"].username,
                    "x": players["bottom"].x,
                    "y": players["bottom"].y,
                    "aim_x": players["bottom"].aim_x,
                    "aim_y": players["bottom"].aim_y,
                    "side": "bottom",
                },
                "p2": {
                    "user_id": players["top"].user_id,
                    "username": players["top"].username,
                    "x": players["top"].x,
                    "y": players["top"].y,
                    "aim_x": players["top"].aim_x,
                    "aim_y": players["top"].aim_y,
                    "side": "top",
                },
                "projectiles": [
                    {
                        "owner_user_id": projectile.owner_user_id,
                        "x": projectile.x,
                        "y": projectile.y,
                        "velocity_x": projectile.velocity_x,
                        "velocity_y": projectile.velocity_y,
                    }
                    for projectile in match.projectiles
                ],
                "obstacles": [
                    {
                        "x": obstacle.x,
                        "y": obstacle.y,
                        "width": obstacle.width,
                        "height": obstacle.height,
                    }
                    for obstacle in match.obstacles
                ],
                "score": {
                    "p1": players["bottom"].hits,
                    "p2": players["top"].hits,
                },
            },
        )

    async def broadcast_hit(self, room: RoomState, match: MatchState, attacker_id: int, target_id: int) -> None:
        attacker = match.players[attacker_id]
        target = match.players[target_id]
        await self.broadcast(
            room,
            "hit",
            {
                "match_id": match.match_id,
                "attacker": attacker_id,
                "target": target_id,
                "score": {
                    "attacker": attacker.hits,
                    "target": target.hits,
                },
            },
        )

    async def broadcast_match_end(self, room: RoomState, match: MatchState) -> None:
        await self.broadcast(
            room,
            "match_end",
            {
                "match_id": match.match_id,
                "winner_user_id": match.winner_user_id,
                "reason": match.end_reason,
            },
        )

    async def broadcast_room_list(self, rooms_payload: list[dict[str, Any]]) -> None:
        for user_id, websocket in list(self.connections_by_user.items()):
            try:
                await websocket.send_json(make_event("room_list_result", {"rooms": rooms_payload}))
            except Exception:
                self.connections_by_user.pop(user_id, None)
