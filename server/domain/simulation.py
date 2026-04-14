from __future__ import annotations

import asyncio
import math
import logging
from datetime import datetime, timezone, timedelta

from server.config import settings
from server.domain.game_config import GameConfigService
from server.domain.matches import MatchRegistry, MatchState, Projectile, Mine
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
                        await self._apply_shield_regen(match)
                        await self._apply_inputs(room, match)
                        await self._advance_mines(room, match)
                        await self._advance_projectiles(room, match)
                await self.connection_manager.broadcast_state(room, match)
        except Exception:
            logger.exception("simulation_loop_failed", extra={"match_id": match.match_id, "room_id": match.room_id})
            raise

    async def _apply_inputs(self, room, match: MatchState) -> None:
        game_settings = await self.game_config.get_settings()
        movement_speed = game_settings["movement_speed"]
        fire_cooldown_ticks = max(1, int(game_settings["fire_cooldown_ticks"]))
        mine_cooldown_ticks = max(1, int(game_settings["mine_cooldown_ticks"]))
        shield_points_max = max(0, int(game_settings["shield_points"]))
        for match_player in match.players.values():
            self._sync_shield_state_for_match(match_player, shield_points_max, match.tick)
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
            if player_state.mine_requested:
                player_state.mine_requested = False
                if (match.tick - match_player.last_mine_tick) >= mine_cooldown_ticks:
                    match_player.last_mine_tick = match.tick
                    match.mines.append(
                        Mine(
                            mine_id=match.next_mine_id,
                            owner_user_id=match_player.user_id,
                            x=match_player.x,
                            y=match_player.y,
                            created_tick=match.tick,
                        )
                    )
                    match.next_mine_id += 1

    async def _advance_mines(self, room, match: MatchState) -> None:
        game_settings = await self.game_config.get_settings()
        hits_to_win = max(1, int(game_settings["hits_to_win"]))
        shield_points_max = max(0, int(game_settings["shield_points"]))
        player_hitbox_radius = game_settings["player_hitbox_radius"]
        mine_hitbox_radius = game_settings["mine_hitbox_radius"]
        hit_distance = player_hitbox_radius + mine_hitbox_radius
        visible_to_all_ticks = settings.ws_tick_rate * 2

        active: list[Mine] = []
        for mine in match.mines:
            if (match.tick - mine.created_tick) < visible_to_all_ticks:
                active.append(mine)
                continue

            target = next(player for player in match.players.values() if player.user_id != mine.owner_user_id)
            if self._visual_distance(mine.x, mine.y, target.x, target.y) <= hit_distance:
                attacker = match.players[mine.owner_user_id]
                life_damage_applied = self._apply_hit_damage(target, shield_points_max, match.tick)
                if life_damage_applied:
                    attacker.hits += 1
                await self.connection_manager.broadcast_hit(
                    room,
                    match,
                    attacker.user_id,
                    target.user_id,
                    "mine",
                    not life_damage_applied,
                )
                if life_damage_applied and attacker.hits >= hits_to_win:
                    await self._finish(match, attacker.user_id, target.user_id, "3_hits")
                    return
                continue
            active.append(mine)
        match.mines = active

    async def _advance_projectiles(self, room, match: MatchState) -> None:
        game_settings = await self.game_config.get_settings()
        hits_to_win = max(1, int(game_settings["hits_to_win"]))
        mine_hits_to_destroy = max(1, int(game_settings["mine_hits_to_destroy"]))
        shield_points_max = max(0, int(game_settings["shield_points"]))
        player_hitbox_radius = game_settings["player_hitbox_radius"]
        projectile_hitbox_radius = game_settings["projectile_hitbox_radius"]
        mine_hitbox_radius = game_settings["mine_hitbox_radius"]
        hit_distance = player_hitbox_radius + projectile_hitbox_radius
        mine_hit_distance = mine_hitbox_radius + projectile_hitbox_radius

        active: list[Projectile] = []
        for projectile in match.projectiles:
            previous_x = projectile.x
            previous_y = projectile.y
            projectile.x += projectile.velocity_x
            projectile.y += projectile.velocity_y
            if projectile.x < 0 or projectile.x > 100 or projectile.y < 0 or projectile.y > 100:
                continue
            if self._collides_with_obstacle_visual(projectile.x, projectile.y, projectile_hitbox_radius, match):
                continue
            enemy_mine_hit = next(
                (
                    mine
                    for mine in match.mines
                    if mine.owner_user_id != projectile.owner_user_id
                    and self._segment_hits_circle_visual(
                        previous_x,
                        previous_y,
                        projectile.x,
                        projectile.y,
                        mine.x,
                        mine.y,
                        mine_hit_distance,
                    )
                ),
                None,
            )
            if enemy_mine_hit is not None:
                enemy_mine_hit.hits_taken += 1
                mine_destroyed = enemy_mine_hit.hits_taken >= mine_hits_to_destroy
                if enemy_mine_hit.hits_taken >= mine_hits_to_destroy:
                    match.mines = [mine for mine in match.mines if mine.mine_id != enemy_mine_hit.mine_id]
                await self.connection_manager.broadcast_mine_hit(
                    room,
                    match,
                    projectile.owner_user_id,
                    enemy_mine_hit.owner_user_id,
                    enemy_mine_hit.mine_id,
                    mine_destroyed,
                )
                continue
            target = next(player for player in match.players.values() if player.user_id != projectile.owner_user_id)
            if self._visual_distance(projectile.x, projectile.y, target.x, target.y) <= hit_distance:
                attacker = match.players[projectile.owner_user_id]
                life_damage_applied = self._apply_hit_damage(target, shield_points_max, match.tick)
                if life_damage_applied:
                    attacker.hits += 1
                await self.connection_manager.broadcast_hit(
                    room,
                    match,
                    attacker.user_id,
                    target.user_id,
                    "projectile",
                    not life_damage_applied,
                )
                if life_damage_applied and attacker.hits >= hits_to_win:
                    await self._finish(match, attacker.user_id, target.user_id, "3_hits")
                    return
                continue
            active.append(projectile)
        match.projectiles = active

    async def _apply_shield_regen(self, match: MatchState) -> None:
        game_settings = await self.game_config.get_settings()
        shield_points_max = max(0, int(game_settings["shield_points"]))
        shield_regen_ticks = max(1, int(game_settings["shield_regen_seconds"]) * settings.ws_tick_rate)
        for player in match.players.values():
            self._sync_shield_state_for_match(player, shield_points_max, match.tick)
            if player.shield_points >= shield_points_max:
                continue
            ticks_since_damage = max(0, match.tick - player.last_damage_tick)
            if ticks_since_damage < shield_regen_ticks:
                continue
            regen_cycles = (ticks_since_damage - shield_regen_ticks) // shield_regen_ticks
            regen_tick = player.last_damage_tick + shield_regen_ticks + (regen_cycles * shield_regen_ticks)
            if regen_tick <= player.last_shield_regen_tick:
                continue
            player.shield_points = min(shield_points_max, player.shield_points + 1)
            player.last_shield_regen_tick = regen_tick

    @staticmethod
    def _sync_shield_state_for_match(player, shield_points_max: int, current_tick: int) -> None:
        if shield_points_max <= 0:
            player.shield_points = 0
            player.last_shield_regen_tick = current_tick
            return
        player.shield_points = max(0, min(shield_points_max, int(player.shield_points)))
        player.last_damage_tick = max(0, int(player.last_damage_tick))
        player.last_shield_regen_tick = max(player.last_damage_tick, int(player.last_shield_regen_tick))

    @staticmethod
    def _apply_hit_damage(target, shield_points_max: int, current_tick: int) -> bool:
        target.last_damage_tick = current_tick
        target.last_shield_regen_tick = current_tick
        if shield_points_max > 0 and target.shield_points > 0:
            target.shield_points = max(0, target.shield_points - 1)
            return False
        return True

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

    def _segment_hits_circle_visual(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        cx: float,
        cy: float,
        radius: float,
    ) -> bool:
        x1v = x1 / self.visual_x_axis_factor
        x2v = x2 / self.visual_x_axis_factor
        cxv = cx / self.visual_x_axis_factor
        dx = x2v - x1v
        dy = y2 - y1
        segment_length_sq = (dx * dx) + (dy * dy)
        if segment_length_sq <= 0:
            return math.hypot(cxv - x1v, cy - y1) <= radius
        t = ((cxv - x1v) * dx + (cy - y1) * dy) / segment_length_sq
        t = max(0.0, min(1.0, t))
        nearest_x = x1v + (dx * t)
        nearest_y = y1 + (dy * t)
        return math.hypot(cxv - nearest_x, cy - nearest_y) <= radius

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
