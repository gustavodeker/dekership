import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Literal
from uuid import uuid4

from .ranking import RankingService
from .rooms import Room
from .simulation import MatchSimulationState, PlayerInput, SimulationEngine
from ..db import get_conn

SendFn = Callable[[int, dict], asyncio.Future | asyncio.Task | None]
BroadcastFn = Callable[[list[int], dict], asyncio.Future | asyncio.Task | None]


@dataclass
class MatchState:
    match_id: str
    room_id: str
    player_bottom_id: int
    player_top_id: int
    status: Literal["playing", "finished"] = "playing"
    score_by_user: dict[int, int] = field(default_factory=dict)
    last_input_by_user: dict[int, PlayerInput] = field(default_factory=dict)
    disconnected_until: dict[int, datetime] = field(default_factory=dict)
    simulation: MatchSimulationState = field(default_factory=MatchSimulationState)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    loop_task: asyncio.Task | None = None


class MatchService:
    def __init__(
        self,
        ranking_service: RankingService,
        tick_rate: int,
        reconnect_timeout_seconds: int,
        send_to_user: SendFn,
        broadcast: BroadcastFn,
    ) -> None:
        self._ranking_service = ranking_service
        self._tick_rate = tick_rate
        self._reconnect_timeout_seconds = reconnect_timeout_seconds
        self._send_to_user = send_to_user
        self._broadcast = broadcast
        self._engine = SimulationEngine()
        self._matches_by_room_id: dict[str, MatchState] = {}
        self._matches_by_id: dict[str, MatchState] = {}

    async def maybe_start_match(self, room: Room) -> MatchState | None:
        if len(room.players) != 2:
            return None
        if room.room_id in self._matches_by_room_id:
            return self._matches_by_room_id[room.room_id]

        bottom = [p for p in room.players.values() if p.side == "bottom"][0]
        top = [p for p in room.players.values() if p.side == "top"][0]

        match = MatchState(
            match_id=str(uuid4()),
            room_id=room.room_id,
            player_bottom_id=bottom.user_id,
            player_top_id=top.user_id,
            score_by_user={bottom.user_id: 0, top.user_id: 0},
            last_input_by_user={bottom.user_id: PlayerInput(), top.user_id: PlayerInput()},
        )

        self._matches_by_room_id[room.room_id] = match
        self._matches_by_id[match.match_id] = match
        await self._persist_match_start(room, match)

        payload = {"event": "match_start", "payload": {"match_id": match.match_id, "tick_rate": self._tick_rate}}
        await self._broadcast([bottom.user_id, top.user_id], payload)

        match.loop_task = asyncio.create_task(self._run_match_loop(match))
        return match

    def get_match_by_room(self, room_id: str) -> MatchState | None:
        return self._matches_by_room_id.get(room_id)

    def get_match_payload(self, match: MatchState) -> dict[str, str | int]:
        return {"match_id": match.match_id, "tick_rate": self._tick_rate}

    async def submit_input(self, match: MatchState, user_id: int, seq: int, move_x: int, shoot: bool) -> bool:
        async with match.lock:
            previous = match.last_input_by_user.get(user_id)
            if previous and seq <= previous.seq:
                return False
            match.last_input_by_user[user_id] = PlayerInput(seq=seq, move_x=move_x, shoot=shoot)
            return True

    async def mark_disconnected(self, match: MatchState, user_id: int) -> None:
        async with match.lock:
            if match.status != "playing":
                return
            match.disconnected_until[user_id] = datetime.utcnow() + timedelta(seconds=self._reconnect_timeout_seconds)

    async def mark_reconnected(self, match: MatchState, user_id: int) -> None:
        async with match.lock:
            match.disconnected_until.pop(user_id, None)

    async def _run_match_loop(self, match: MatchState) -> None:
        interval = 1 / max(1, self._tick_rate)
        while True:
            await asyncio.sleep(interval)
            async with match.lock:
                if match.status != "playing":
                    return

                now = datetime.utcnow()
                expired = [uid for uid, deadline in match.disconnected_until.items() if now >= deadline]
                if expired:
                    loser = expired[0]
                    winner = match.player_top_id if loser == match.player_bottom_id else match.player_bottom_id
                    await self._finish_match(match, winner, loser, "disconnect", disconnect_loser=True)
                    return

                bottom_input = match.last_input_by_user[match.player_bottom_id]
                top_input = match.last_input_by_user[match.player_top_id]
                snapshot, hits = self._engine.step(
                    match.simulation,
                    match.player_bottom_id,
                    match.player_top_id,
                    bottom_input,
                    top_input,
                )

                for attacker, target in hits:
                    match.score_by_user[attacker] += 1
                    await self._broadcast(
                        [match.player_bottom_id, match.player_top_id],
                        {
                            "event": "hit",
                            "payload": {
                                "match_id": match.match_id,
                                "attacker": attacker,
                                "target": target,
                                "score": {
                                    "attacker": match.score_by_user[attacker],
                                    "target": match.score_by_user[target],
                                },
                            },
                        },
                    )

                snapshot.score = {
                    "p1": match.score_by_user[match.player_bottom_id],
                    "p2": match.score_by_user[match.player_top_id],
                }
                await self._broadcast(
                    [match.player_bottom_id, match.player_top_id],
                    {
                        "event": "state",
                        "payload": {
                            "tick": snapshot.tick,
                            "p1": snapshot.p1,
                            "p2": snapshot.p2,
                            "projectiles": snapshot.projectiles,
                            "score": snapshot.score,
                        },
                    },
                )

                for uid, score in match.score_by_user.items():
                    if score >= 3:
                        loser = match.player_top_id if uid == match.player_bottom_id else match.player_bottom_id
                        await self._finish_match(match, uid, loser, "3_hits")
                        return

    async def _finish_match(
        self,
        match: MatchState,
        winner_user_id: int,
        loser_user_id: int,
        reason: str,
        disconnect_loser: bool = False,
    ) -> None:
        match.status = "finished"
        await self._ranking_service.persist_match_result(
            match_uuid=match.match_id,
            winner_user_id=winner_user_id,
            loser_user_id=loser_user_id,
            end_reason=reason,
            disconnect_loser=disconnect_loser,
        )
        await self._broadcast(
            [match.player_bottom_id, match.player_top_id],
            {
                "event": "match_end",
                "payload": {
                    "match_id": match.match_id,
                    "winner_user_id": winner_user_id,
                    "reason": reason,
                },
            },
        )

    async def _persist_match_start(self, room: Room, match: MatchState) -> None:
        query = (
            "INSERT INTO game_match (match_uuid, room_id, player_bottom_id, player_top_id, status, started_at) "
            "SELECT %s, id, %s, %s, 'playing', %s FROM game_room WHERE room_uuid = %s LIMIT 1"
        )
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query,
                    (
                        match.match_id,
                        match.player_bottom_id,
                        match.player_top_id,
                        datetime.utcnow(),
                        room.room_id,
                    ),
                )
            await conn.commit()
