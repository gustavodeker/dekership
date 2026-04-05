from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from server.db import get_pool


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class PlayerState:
    user_id: int
    username: str
    side: str
    websocket: Any | None = None
    connected: bool = False
    input_seq: int = -1
    move_x: int = 0
    move_y: int = 0
    aim_x: float = 50.0
    aim_y: float = 50.0
    shoot_requested: bool = False
    disconnect_started_at: datetime | None = None


@dataclass(slots=True)
class RoomState:
    room_id: str
    name: str
    status: str
    created_by_user_id: int
    created_at: datetime
    room_db_id: int | None = None
    players: dict[int, PlayerState] = field(default_factory=dict)
    match_id: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RoomRegistry:
    def __init__(self) -> None:
        self.rooms: dict[str, RoomState] = {}
        self.room_ids_by_user: dict[int, str] = {}
        self.lock = asyncio.Lock()

    async def list_rooms(self) -> list[dict[str, Any]]:
        async with self.lock:
            return self._list_rooms_unlocked()

    async def get_room(self, room_id: str) -> RoomState | None:
        async with self.lock:
            return self.rooms.get(room_id)

    async def get_room_for_user(self, user_id: int) -> RoomState | None:
        async with self.lock:
            room_id = self.room_ids_by_user.get(user_id)
            if room_id is None:
                return None
            return self.rooms.get(room_id)

    def _list_rooms_unlocked(self) -> list[dict[str, Any]]:
        return [
            {
                "room_id": room.room_id,
                "name": room.name,
                "players": len(room.players),
                "status": room.status,
            }
            for room in self.rooms.values()
            if room.status == "waiting" and len(room.players) < 2
        ]

    async def create_room(self, created_by_user_id: int, room_name: str) -> RoomState:
        async with self.lock:
            room_id = str(uuid4())
            room = RoomState(
                room_id=room_id,
                name=room_name,
                status="waiting",
                created_by_user_id=created_by_user_id,
                created_at=utcnow(),
            )
            self.rooms[room_id] = room
            return room

    def _leave_room_unlocked(self, user_id: int) -> tuple[RoomState | None, bool]:
        room_id = self.room_ids_by_user.get(user_id)
        if room_id is None:
            return None, False
        room = self.rooms.get(room_id)
        if room is None:
            self.room_ids_by_user.pop(user_id, None)
            return None, False

        is_creator = room.created_by_user_id == user_id
        self.room_ids_by_user.pop(user_id, None)
        room.players.pop(user_id, None)

        if is_creator:
            room.status = "closed"
            self.rooms.pop(room_id, None)
            for other_user_id in list(room.players):
                self.room_ids_by_user.pop(other_user_id, None)
            return room, True

        if not room.players:
            room.status = "closed"
            self.rooms.pop(room_id, None)
            return room, True

        return room, False

    async def leave_room(self, user_id: int) -> tuple[RoomState | None, bool]:
        async with self.lock:
            return self._leave_room_unlocked(user_id)

    async def join_room(
        self,
        room_id: str,
        user_id: int,
        username: str,
        websocket: Any,
    ) -> tuple[RoomState, PlayerState, bool, list[RoomState]]:
        closed_rooms: list[RoomState] = []
        async with self.lock:
            if user_id in self.room_ids_by_user:
                current_room = self.rooms.get(self.room_ids_by_user[user_id])
                if current_room and current_room.room_id == room_id:
                    player = current_room.players[user_id]
                    player.websocket = websocket
                    player.connected = True
                    player.disconnect_started_at = None
                    player.input_seq = -1
                    player.move_x = 0
                    player.move_y = 0
                    player.shoot_requested = False
                    return current_room, player, False, closed_rooms
                _, room_closed = self._leave_room_unlocked(user_id)
                if room_closed and current_room is not None:
                    closed_rooms.append(current_room)

            room = self.rooms.get(room_id)
            if room is None:
                raise ValueError("ROOM_NOT_FOUND")
            if len(room.players) >= 2:
                raise ValueError("ROOM_FULL")
            side = "bottom" if not room.players else "top"
            player = PlayerState(
                user_id=user_id,
                username=username,
                side=side,
                websocket=websocket,
                connected=True,
            )
            room.players[user_id] = player
            self.room_ids_by_user[user_id] = room_id
            return room, player, True, closed_rooms

    async def attach_existing_connection(self, user_id: int, websocket: Any) -> RoomState | None:
        async with self.lock:
            room_id = self.room_ids_by_user.get(user_id)
            if room_id is None:
                return None
            room = self.rooms.get(room_id)
            if room is None:
                return None
            player = room.players.get(user_id)
            if player is None:
                return None
            player.websocket = websocket
            player.connected = True
            player.disconnect_started_at = None
            player.input_seq = -1
            player.move_x = 0
            player.move_y = 0
            player.shoot_requested = False
            return room

    async def mark_disconnected(self, user_id: int) -> RoomState | None:
        async with self.lock:
            room_id = self.room_ids_by_user.get(user_id)
            if room_id is None:
                return None
            room = self.rooms.get(room_id)
            if room is None:
                return None
            player = room.players.get(user_id)
            if player is None:
                return None
            player.connected = False
            player.websocket = None
            player.disconnect_started_at = utcnow()
            return room

    async def close_room(self, room_id: str) -> None:
        async with self.lock:
            room = self.rooms.get(room_id)
            if room is None:
                return
            room.status = "closed"

    async def remove_room(self, room_id: str) -> None:
        async with self.lock:
            room = self.rooms.pop(room_id, None)
            if room is None:
                return
            for user_id in room.players:
                self.room_ids_by_user.pop(user_id, None)


async def persist_room_created(room: RoomState) -> None:
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO game_room (room_uuid, name, status, created_by_user_id, created_at)
                VALUES (%s, %s, 'waiting', %s, %s)
                """,
                (
                    room.room_id,
                    room.name,
                    room.created_by_user_id,
                    room.created_at.replace(tzinfo=None),
                ),
            )
            room.room_db_id = int(cursor.lastrowid)
            await connection.commit()


async def persist_room_started(room: RoomState) -> None:
    if room.room_db_id is None:
        return
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE game_room
                SET status = 'playing', started_at = UTC_TIMESTAMP()
                WHERE id = %s
                """,
                (room.room_db_id,),
            )
            await connection.commit()


async def persist_room_closed(room: RoomState) -> None:
    if room.room_db_id is None:
        return
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE game_room
                SET status = 'closed', closed_at = UTC_TIMESTAMP()
                WHERE id = %s
                """,
                (room.room_db_id,),
            )
            await connection.commit()
