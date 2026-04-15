from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
import math

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
        pause_remaining_seconds = 0
        if match.paused_until is not None:
            pause_remaining_seconds = max(
                0,
                math.ceil((match.paused_until - datetime.now(timezone.utc)).total_seconds()),
            )
        shared_payload = {
            "tick": match.tick,
            "paused": match.paused_until is not None,
            "pause_remaining_seconds": pause_remaining_seconds,
            "pause_disconnected_user_id": match.paused_by_user_id,
            "p1": {
                "user_id": players["bottom"].user_id,
                "username": players["bottom"].username,
                "x": players["bottom"].x,
                "y": players["bottom"].y,
                "aim_x": players["bottom"].aim_x,
                "aim_y": players["bottom"].aim_y,
                "side": "bottom",
                "last_mine_tick": players["bottom"].last_mine_tick,
                "shield_points": players["bottom"].shield_points,
                "last_damage_tick": players["bottom"].last_damage_tick,
                "last_shield_regen_tick": players["bottom"].last_shield_regen_tick,
            },
            "p2": {
                "user_id": players["top"].user_id,
                "username": players["top"].username,
                "x": players["top"].x,
                "y": players["top"].y,
                "aim_x": players["top"].aim_x,
                "aim_y": players["top"].aim_y,
                "side": "top",
                "last_mine_tick": players["top"].last_mine_tick,
                "shield_points": players["top"].shield_points,
                "last_damage_tick": players["top"].last_damage_tick,
                "last_shield_regen_tick": players["top"].last_shield_regen_tick,
            },
            "projectiles": [
                {
                    "projectile_id": projectile.projectile_id,
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
        }
        for room_player in room.players.values():
            if not room_player.connected or room_player.websocket is None:
                continue
            payload = {
                **shared_payload,
                "mines": [
                    {
                        "mine_id": mine.mine_id,
                        "owner_user_id": mine.owner_user_id,
                        "x": mine.x,
                        "y": mine.y,
                        "created_tick": mine.created_tick,
                        "hits_taken": mine.hits_taken,
                    }
                    for mine in match.mines
                ],
            }
            await self.send_json(room_player.websocket, "state", payload)

    async def broadcast_hit(
        self,
        room: RoomState,
        match: MatchState,
        attacker_id: int,
        target_id: int,
        source: str = "projectile",
        shield_blocked: bool = False,
    ) -> None:
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
                "source": source,
                "shield_blocked": shield_blocked,
            },
        )

    async def broadcast_mine_hit(
        self,
        room: RoomState,
        match: MatchState,
        attacker_id: int,
        mine_owner_id: int,
        mine_id: int,
        destroyed: bool,
    ) -> None:
        await self.broadcast(
            room,
            "mine_hit",
            {
                "match_id": match.match_id,
                "attacker": attacker_id,
                "mine_owner": mine_owner_id,
                "mine_id": mine_id,
                "destroyed": destroyed,
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

    async def broadcast_open_world_state(self, open_world_state, tick_rate: int) -> None:
        payload = {
            "world_id": open_world_state.world_id,
            "tick": open_world_state.tick,
            "tick_rate": tick_rate,
            "max_players": open_world_state.max_players,
            "players": [
                {
                    "user_id": player.user_id,
                    "username": player.username,
                    "x": player.x,
                    "y": player.y,
                    "aim_x": player.aim_x,
                    "aim_y": player.aim_y,
                    "kills": player.kills,
                    "deaths": player.deaths,
                    "damage_taken": player.damage_taken,
                    "shield_points": player.shield_points,
                    "last_mine_tick": player.last_mine_tick,
                    "last_damage_tick": player.last_damage_tick,
                    "last_shield_regen_tick": player.last_shield_regen_tick,
                    "alive": player.alive,
                    "dead_until_tick": player.dead_until_tick,
                    "invulnerable_until_tick": player.invulnerable_until_tick,
                    "target_kind": player.target_kind,
                    "target_id": player.target_id,
                }
                for player in open_world_state.players.values()
            ],
            "projectiles": [
                {
                    "projectile_id": projectile.projectile_id,
                    "owner_user_id": projectile.owner_user_id,
                    "owner_kind": projectile.owner_kind,
                    "owner_entity_id": projectile.owner_entity_id,
                    "target_kind": projectile.target_kind,
                    "target_entity_id": projectile.target_entity_id,
                    "x": projectile.x,
                    "y": projectile.y,
                    "velocity_x": projectile.velocity_x,
                    "velocity_y": projectile.velocity_y,
                }
                for projectile in open_world_state.projectiles
            ],
            "monsters": [
                {
                    "monster_id": monster.monster_id,
                    "x": monster.x,
                    "y": monster.y,
                    "name": monster.name,
                    "target_player_id": monster.target_player_id,
                    "aim_x": monster.aim_x,
                    "aim_y": monster.aim_y,
                    "hp": monster.hp,
                    "max_hp": monster.max_hp,
                }
                for monster in open_world_state.monsters.values()
            ],
            "mines": [
                {
                    "mine_id": mine.mine_id,
                    "owner_user_id": mine.owner_user_id,
                    "x": mine.x,
                    "y": mine.y,
                    "created_tick": mine.created_tick,
                    "hits_taken": mine.hits_taken,
                }
                for mine in open_world_state.mines
            ],
            "obstacles": [
                {
                    "x": obstacle.x,
                    "y": obstacle.y,
                    "width": obstacle.width,
                    "height": obstacle.height,
                }
                for obstacle in open_world_state.obstacles
            ],
        }
        for player in open_world_state.players.values():
            websocket = self.connections_by_user.get(player.user_id)
            if websocket is None:
                continue
            await self.send_json(websocket, "open_world_state", payload)

    async def broadcast_open_world_hit(
        self,
        open_world_state,
        attacker_id: int,
        target_id: int,
        source: str,
        shield_blocked: bool,
        attacker_kind: str = "player",
        attacker_monster_id: int | None = None,
    ) -> None:
        payload = {
            "attacker": attacker_id,
            "attacker_kind": attacker_kind,
            "attacker_monster_id": attacker_monster_id,
            "target": target_id,
            "source": source,
            "shield_blocked": shield_blocked,
        }
        for player in open_world_state.players.values():
            websocket = self.connections_by_user.get(player.user_id)
            if websocket is None:
                continue
            await self.send_json(websocket, "open_world_hit", payload)

    async def broadcast_open_world_mine_hit(
        self,
        open_world_state,
        attacker_id: int,
        mine_owner_id: int,
        mine_id: int,
        destroyed: bool,
    ) -> None:
        payload = {
            "attacker": attacker_id,
            "mine_owner": mine_owner_id,
            "mine_id": mine_id,
            "destroyed": destroyed,
        }
        for player in open_world_state.players.values():
            websocket = self.connections_by_user.get(player.user_id)
            if websocket is None:
                continue
            await self.send_json(websocket, "open_world_mine_hit", payload)

    async def broadcast_open_world_death(
        self,
        open_world_state,
        target_id: int,
        killer_id: int,
        respawn_seconds: int,
    ) -> None:
        payload = {
            "target_id": target_id,
            "killer_id": killer_id,
            "respawn_seconds": respawn_seconds,
        }
        for player in open_world_state.players.values():
            websocket = self.connections_by_user.get(player.user_id)
            if websocket is None:
                continue
            await self.send_json(websocket, "open_world_death", payload)

    async def broadcast_open_world_monster_hit(
        self,
        open_world_state,
        monster_id: int,
        hp: int,
        max_hp: int,
        destroyed: bool,
        x: float,
        y: float,
    ) -> None:
        payload = {
            "monster_id": monster_id,
            "hp": hp,
            "max_hp": max_hp,
            "destroyed": destroyed,
            "x": x,
            "y": y,
        }
        for player in open_world_state.players.values():
            websocket = self.connections_by_user.get(player.user_id)
            if websocket is None:
                continue
            await self.send_json(websocket, "open_world_monster_hit", payload)
