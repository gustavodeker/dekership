from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from server.db import get_pool
from server.domain.rooms import RoomState


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class MatchPlayer:
    user_id: int
    username: str
    side: str
    x: float
    y: float
    aim_x: float
    aim_y: float
    hits: int = 0
    last_shot_tick: int = 0


@dataclass(slots=True)
class Projectile:
    owner_user_id: int
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    speed: float = 1.6


@dataclass(slots=True)
class Obstacle:
    x: float
    y: float
    width: float
    height: float


@dataclass(slots=True)
class MatchState:
    match_id: str
    room_id: str
    room_db_id: int | None
    tick: int = 0
    status: str = "playing"
    winner_user_id: int | None = None
    loser_user_id: int | None = None
    end_reason: str | None = None
    players: dict[int, MatchPlayer] = field(default_factory=dict)
    projectiles: list[Projectile] = field(default_factory=list)
    obstacles: list[Obstacle] = field(default_factory=list)
    task: asyncio.Task | None = None
    started_at: datetime = field(default_factory=utcnow)
    finished_at: datetime | None = None


class MatchRegistry:
    def __init__(self) -> None:
        self.matches: dict[str, MatchState] = {}
        self.room_to_match: dict[str, str] = {}
        self.lock = asyncio.Lock()

    async def start_match(self, room: RoomState, room_db_id: int | None = None) -> MatchState:
        async with self.lock:
            match_id = str(uuid4())
            players = list(room.players.values())
            bottom = next(player for player in players if player.side == "bottom")
            top = next(player for player in players if player.side == "top")
            state = MatchState(
                match_id=match_id,
                room_id=room.room_id,
                room_db_id=room_db_id,
                obstacles=[
                    Obstacle(x=44.0, y=35.0, width=12.0, height=30.0),
                    Obstacle(x=20.0, y=45.0, width=10.0, height=14.0),
                    Obstacle(x=70.0, y=45.0, width=10.0, height=14.0),
                ],
                players={
                    bottom.user_id: MatchPlayer(bottom.user_id, bottom.username, "bottom", 50.0, 82.0, 50.0, 0.0),
                    top.user_id: MatchPlayer(top.user_id, top.username, "top", 50.0, 18.0, 50.0, 100.0),
                },
            )
            self.matches[match_id] = state
            self.room_to_match[room.room_id] = match_id
            room.match_id = match_id
            room.status = "playing"
            return state

    async def get_by_room(self, room_id: str) -> MatchState | None:
        async with self.lock:
            match_id = self.room_to_match.get(room_id)
            if match_id is None:
                return None
            return self.matches.get(match_id)

    async def finish_match(
        self,
        match: MatchState,
        winner_user_id: int,
        loser_user_id: int,
        reason: str,
        disconnected_user_id: int | None = None,
    ) -> None:
        if match.status == "finished":
            return
        match.status = "finished"
        match.winner_user_id = winner_user_id
        match.loser_user_id = loser_user_id
        match.end_reason = reason
        match.finished_at = utcnow()

        pool = get_pool()
        async with pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    await cursor.execute("START TRANSACTION")
                    if match.room_db_id is not None:
                        await cursor.execute(
                            """
                            INSERT INTO game_match (
                                match_uuid, room_id, player_bottom_id, player_top_id, winner_user_id,
                                loser_user_id, end_reason, status, started_at, ended_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, 'finished', %s, %s)
                            ON DUPLICATE KEY UPDATE
                                winner_user_id = VALUES(winner_user_id),
                                loser_user_id = VALUES(loser_user_id),
                                end_reason = VALUES(end_reason),
                                status = 'finished',
                                ended_at = VALUES(ended_at)
                            """,
                            (
                                match.match_id,
                                match.room_db_id,
                                self._player_by_side(match, "bottom").user_id,
                                self._player_by_side(match, "top").user_id,
                                winner_user_id,
                                loser_user_id,
                                reason,
                                match.started_at.replace(tzinfo=None),
                                match.finished_at.replace(tzinfo=None),
                            ),
                        )
                    await self._upsert_stats(cursor, winner_user_id, 1, 0, 0)
                    await self._upsert_stats(
                        cursor,
                        loser_user_id,
                        0,
                        1,
                        1 if disconnected_user_id == loser_user_id else 0,
                    )
                    await connection.commit()
                except Exception:
                    await connection.rollback()
                    raise

    async def remove_match(self, match_id: str) -> None:
        async with self.lock:
            match = self.matches.pop(match_id, None)
            if match is None:
                return
            self.room_to_match.pop(match.room_id, None)

    @staticmethod
    async def _upsert_stats(cursor, user_id: int, wins: int, losses: int, disconnects: int) -> None:
        await cursor.execute(
            """
            INSERT INTO player_stats (user_id, wins, losses, disconnects, updated_at)
            VALUES (%s, %s, %s, %s, UTC_TIMESTAMP())
            ON DUPLICATE KEY UPDATE
                wins = wins + VALUES(wins),
                losses = losses + VALUES(losses),
                disconnects = disconnects + VALUES(disconnects),
                updated_at = UTC_TIMESTAMP()
            """,
            (user_id, wins, losses, disconnects),
        )

    @staticmethod
    def _player_by_side(match: MatchState, side: str) -> MatchPlayer:
        return next(player for player in match.players.values() if player.side == side)
