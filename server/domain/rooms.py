import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

from ..db import get_conn


RoomStatus = Literal["waiting", "playing", "closed"]


@dataclass
class RoomPlayer:
    user_id: int
    username: str
    side: Literal["bottom", "top"]


@dataclass
class Room:
    room_id: str
    name: str
    created_by_user_id: int
    status: RoomStatus = "waiting"
    players: dict[int, RoomPlayer] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    db_id: int | None = None


class RoomService:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._lock = asyncio.Lock()

    async def create_room(self, room_name: str, creator_user_id: int) -> Room:
        room = Room(room_id=str(uuid4()), name=room_name, created_by_user_id=creator_user_id)
        async with self._lock:
            self._rooms[room.room_id] = room
        await self._persist_room(room)
        return room

    async def list_open_rooms(self) -> list[Room]:
        async with self._lock:
            return [r for r in self._rooms.values() if r.status == "waiting" and len(r.players) < 2]

    async def get_room(self, room_id: str) -> Room | None:
        async with self._lock:
            return self._rooms.get(room_id)

    async def find_room_by_player(self, user_id: int) -> Room | None:
        async with self._lock:
            for room in self._rooms.values():
                if user_id in room.players:
                    return room
        return None

    async def join_room(self, room: Room, user_id: int, username: str) -> RoomPlayer:
        async with room.lock:
            if user_id in room.players:
                return room.players[user_id]
            if room.status != "waiting":
                raise ValueError("INVALID_STATE")
            if len(room.players) >= 2:
                raise ValueError("ROOM_FULL")

            side: Literal["bottom", "top"] = "bottom" if len(room.players) == 0 else "top"
            player = RoomPlayer(user_id=user_id, username=username, side=side)
            room.players[user_id] = player
            return player

    async def set_room_playing(self, room: Room) -> None:
        async with room.lock:
            room.status = "playing"
        await self._update_room_status(room, "playing", started_at=True)

    async def close_room(self, room: Room) -> None:
        async with room.lock:
            room.status = "closed"
        await self._update_room_status(room, "closed", closed_at=True)

    async def _persist_room(self, room: Room) -> None:
        query = (
            "INSERT INTO game_room (room_uuid, name, status, created_by_user_id, created_at) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (room.room_id, room.name, room.status, room.created_by_user_id, datetime.utcnow()))
                room.db_id = int(cur.lastrowid)
            await conn.commit()

    async def _update_room_status(self, room: Room, status: str, started_at: bool = False, closed_at: bool = False) -> None:
        set_parts = ["status = %s"]
        params: list[object] = [status]
        if started_at:
            set_parts.append("started_at = %s")
            params.append(datetime.utcnow())
        if closed_at:
            set_parts.append("closed_at = %s")
            params.append(datetime.utcnow())

        params.append(room.room_id)
        query = f"UPDATE game_room SET {', '.join(set_parts)} WHERE room_uuid = %s"
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, tuple(params))
            await conn.commit()
