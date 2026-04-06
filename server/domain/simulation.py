from __future__ import annotations

import asyncio
import math
import logging
from datetime import datetime, timezone, timedelta

from server.config import settings
from server.domain.game_config import GameConfigService
from server.domain.matches import MatchRegistry, MatchState, Projectile
from server.domain.rooms import RoomRegistry, persist_room_closed
from server.ws.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class SimulationService:
    def __init__(
        self,
        room_registry: RoomRegistry,
        match_registry: MatchRegistry,
        connection_manager: ConnectionManager,
        game_config: GameConfigService,
    ) -> None:
        self.room_registry = room_registry
        self.match_registry = match_registry
        self.connection_manager = connection_manager
        self.game_config = game_config
        self.tick_interval = 1 / settings.ws_tick_rate
        self.arena_min_x = 0.0
        self.arena_max_x = 100.0
        self.arena_min_y = 0.0
        self.arena_max_y = 100.0
        self.player_collision_radius = 2.8
        self.visual_x_axis_factor = 768.0 / 1366.0

    async def start(self, match: MatchState) -> None:
        match.task = asyncio.create_task(self._run(match))

    async def _run(self, match: MatchState) -> None:
        try:
            while match.status == "playing":
                await asyncio.sleep(self.tick_interval)
                match.tick += 1
                room = await self.room_registry.get_room(match.room_id)
                if room is None:
                    break
                paused_remaining = self._pause_remaining_seconds(match)
                if paused_remaining is not None:
                    if self._is_connected(room, match.paused_by_user_id):
                        match.paused_by_user_id = None
                        match.paused_until = None
                    elif paused_remaining <= 0 and match.paused_by_user_id is not None:
                        disconnected = match.paused_by_user_id
                        winner = next(user_id for user_id in match.players if user_id != disconnected)
                        await self._finish(match, winner, disconnected, "disconnect", disconnected)
                        break
                else:
                    disconnected = self._first_disconnected_user(room)
                    if disconnected is not None:
                        match.paused_by_user_id = disconnected
                        match.paused_until = datetime.now(timezone.utc) + timedelta(
                            seconds=settings.reconnect_timeout_seconds
                        )
                    else:
                        await self._apply_inputs(room, match)
                        await self._advance_projectiles(room, match)
                await self.connection_manager.broadcast_state(room, match)
        except Exception:
            logger.exception("simulation_loop_failed", extra={"match_id": match.match_id, "room_id": match.room_id})
            raise

    async def _apply_inputs(self, room, match: MatchState) -> None:
        game_settings = await self.game_config.get_settings()
        movement_speed = game_settings["movement_speed"]
        fire_cooldown_ticks = max(1, int(game_settings["fire_cooldown_ticks"]))
        for player_state in room.players.values():
            match_player = match.players[player_state.user_id]
            input_x = float(player_state.move_x)
            input_y = float(player_state.move_y)
            input_magnitude = math.hypot(input_x, input_y)
            if input_magnitude > 0.0:
                input_x /= input_magnitude
                input_y /= input_magnitude

            move_x = input_x * self.visual_x_axis_factor
            move_y = input_y

            next_x = max(
                self.arena_min_x,
                min(self.arena_max_x, match_player.x + (move_x * movement_speed)),
            )
            if not self._collides_with_obstacle(next_x, match_player.y, self.player_collision_radius, match):
                match_player.x = next_x

            next_y = max(
                self.arena_min_y,
                min(self.arena_max_y, match_player.y + (move_y * movement_speed)),
            )
            if not self._collides_with_obstacle(match_player.x, next_y, self.player_collision_radius, match):
                match_player.y = next_y
            match_player.aim_x = player_state.aim_x
            match_player.aim_y = player_state.aim_y
            if player_state.shoot_requested:
                player_state.shoot_requested = False
                if (match.tick - match_player.last_shot_tick) >= fire_cooldown_ticks:
                    delta_x = match_player.aim_x - match_player.x
                    delta_y = match_player.aim_y - match_player.y
                    distance = math.hypot(delta_x, delta_y) or 1.0
                    match_player.last_shot_tick = match.tick
                    match.projectiles.append(
                        Projectile(
                            projectile_id=match.next_projectile_id,
                            owner_user_id=match_player.user_id,
                            x=match_player.x,
                            y=match_player.y,
                            velocity_x=(delta_x / distance) * game_settings["projectile_speed"],
                            velocity_y=(delta_y / distance) * game_settings["projectile_speed"],
                            speed=game_settings["projectile_speed"],
                        )
                    )
                    match.next_projectile_id += 1

    async def _advance_projectiles(self, room, match: MatchState) -> None:
        game_settings = await self.game_config.get_settings()
        hits_to_win = max(1, int(game_settings["hits_to_win"]))
        player_hitbox_radius = game_settings["player_hitbox_radius"]
        projectile_hitbox_radius = game_settings["projectile_hitbox_radius"]
        hit_distance = player_hitbox_radius + projectile_hitbox_radius

        active: list[Projectile] = []
        for projectile in match.projectiles:
            projectile.x += projectile.velocity_x
            projectile.y += projectile.velocity_y
            if projectile.x < 0 or projectile.x > 100 or projectile.y < 0 or projectile.y > 100:
                continue
            if self._collides_with_obstacle_visual(projectile.x, projectile.y, projectile_hitbox_radius, match):
                continue
            target = next(player for player in match.players.values() if player.user_id != projectile.owner_user_id)
            if self._visual_distance(projectile.x, projectile.y, target.x, target.y) <= hit_distance:
                attacker = match.players[projectile.owner_user_id]
                attacker.hits += 1
                await self.connection_manager.broadcast_hit(room, match, attacker.user_id, target.user_id)
                if attacker.hits >= hits_to_win:
                    await self._finish(match, attacker.user_id, target.user_id, "3_hits")
                    return
                continue
            active.append(projectile)
        match.projectiles = active

    @staticmethod
    def _collides_with_obstacle(x: float, y: float, radius: float, match: MatchState) -> bool:
        for obstacle in match.obstacles:
            closest_x = max(obstacle.x, min(x, obstacle.x + obstacle.width))
            closest_y = max(obstacle.y, min(y, obstacle.y + obstacle.height))
            if math.hypot(x - closest_x, y - closest_y) <= radius:
                return True
        return False

    def _visual_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        dx = (x1 - x2) / self.visual_x_axis_factor
        dy = y1 - y2
        return math.hypot(dx, dy)

    def _collides_with_obstacle_visual(self, x: float, y: float, radius: float, match: MatchState) -> bool:
        for obstacle in match.obstacles:
            closest_x = max(obstacle.x, min(x, obstacle.x + obstacle.width))
            closest_y = max(obstacle.y, min(y, obstacle.y + obstacle.height))
            if self._visual_distance(x, y, closest_x, closest_y) <= radius:
                return True
        return False

    @staticmethod
    def _first_disconnected_user(room) -> int | None:
        for player in room.players.values():
            if not player.connected:
                return player.user_id
        return None

    @staticmethod
    def _is_connected(room, user_id: int | None) -> bool:
        if user_id is None:
            return False
        player = room.players.get(user_id)
        if player is None:
            return False
        return bool(player.connected and player.websocket is not None)

    @staticmethod
    def _pause_remaining_seconds(match: MatchState) -> int | None:
        if match.paused_until is None:
            return None
        remaining = math.ceil((match.paused_until - datetime.now(timezone.utc)).total_seconds())
        return max(0, remaining)

    async def _finish(
        self,
        match: MatchState,
        winner_user_id: int,
        loser_user_id: int,
        reason: str,
        disconnected_user_id: int | None = None,
    ) -> None:
        await self.match_registry.finish_match(match, winner_user_id, loser_user_id, reason, disconnected_user_id)
        room = await self.room_registry.get_room(match.room_id)
        if room is not None:
            room.status = "finished"
            await self.connection_manager.broadcast_match_end(room, match)
            await self.room_registry.close_room(room.room_id)
            await persist_room_closed(room)
            await self.room_registry.remove_room(room.room_id)
        await self.match_registry.remove_match(match.match_id)
