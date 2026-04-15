from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass, field

from server.config import settings
from server.domain.game_config import GameConfigService
from server.domain.matches import Mine, Obstacle, Projectile
from server.ws.connection_manager import ConnectionManager


@dataclass(slots=True)
class OpenWorldPlayer:
    user_id: int
    username: str
    x: float
    y: float
    aim_x: float = 50.0
    aim_y: float = 50.0
    connected: bool = True
    input_seq: int = -1
    move_x: int = 0
    move_y: int = 0
    shoot_requested: bool = False
    mine_requested: bool = False
    kills: int = 0
    deaths: int = 0
    damage_taken: int = 0
    shield_points: int = 2
    last_damage_tick: int = 0
    last_shield_regen_tick: int = 0
    last_shot_tick: int = 0
    last_mine_tick: int = -1000000
    alive: bool = True
    dead_until_tick: int = 0
    invulnerable_until_tick: int = 0
    target_kind: str | None = None
    target_id: int | None = None


@dataclass(slots=True)
class OpenWorldMonster:
    monster_id: int
    x: float
    y: float
    aim_x: float
    aim_y: float
    hp: int
    max_hp: int
    move_target_x: float
    move_target_y: float
    last_shot_tick: int = 0
    last_retarget_tick: int = 0


@dataclass(slots=True)
class OpenWorldState:
    world_id: str = "global"
    max_players: int = 50
    tick: int = 0
    players: dict[int, OpenWorldPlayer] = field(default_factory=dict)
    monsters: dict[int, OpenWorldMonster] = field(default_factory=dict)
    pending_monster_respawns: list[int] = field(default_factory=list)
    projectiles: list[Projectile] = field(default_factory=list)
    mines: list[Mine] = field(default_factory=list)
    obstacles: list[Obstacle] = field(
        default_factory=lambda: [
            Obstacle(x=44.0, y=35.0, width=12.0, height=30.0),
            Obstacle(x=20.0, y=45.0, width=10.0, height=14.0),
            Obstacle(x=70.0, y=45.0, width=10.0, height=14.0),
        ]
    )
    next_projectile_id: int = 1
    next_mine_id: int = 1
    next_monster_id: int = 1
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class OpenWorldService:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        game_config: GameConfigService,
        max_players: int = 50,
    ) -> None:
        self.connection_manager = connection_manager
        self.game_config = game_config
        self.max_players = max_players
        self.tick_rate = max(1, int(settings.ws_tick_rate))
        self.tick_interval = 1 / self.tick_rate
        self.player_collision_radius = 2.8
        self.monster_collision_radius = 2.8
        self.visual_x_axis_factor = 768.0 / 1366.0
        self.camera_zoom_factor = 2.0
        self.visual_speed_factor = 1.0 / self.camera_zoom_factor
        self.state = OpenWorldState()
        self.state.max_players = max_players
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        if self.task is not None and not self.task.done():
            return
        self.task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self.task is None:
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        self.task = None

    async def has_player(self, user_id: int) -> bool:
        async with self.state.lock:
            return user_id in self.state.players

    async def join(self, user_id: int, username: str) -> OpenWorldPlayer:
        async with self.state.lock:
            existing = self.state.players.get(user_id)
            if existing is not None:
                existing.connected = True
                existing.username = username
                return existing
            if len(self.state.players) >= self.max_players:
                raise ValueError("WORLD_FULL")
            game_settings = await self.game_config.get_settings("open_world")
            shield_points_max = max(0, int(game_settings["shield_points"]))
            spawn_x, spawn_y = self._random_spawn_position()
            player = OpenWorldPlayer(
                user_id=user_id,
                username=username,
                x=spawn_x,
                y=spawn_y,
                shield_points=shield_points_max,
                last_damage_tick=self.state.tick,
                last_shield_regen_tick=self.state.tick,
            )
            self.state.players[user_id] = player
            return player

    async def leave(self, user_id: int) -> bool:
        async with self.state.lock:
            player = self.state.players.pop(user_id, None)
            if player is None:
                return False
            return True

    async def apply_input(
        self,
        user_id: int,
        seq: int,
        move_x: int,
        move_y: int,
        aim_x: float,
        aim_y: float,
        shoot: bool,
        drop_mine: bool,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> bool:
        async with self.state.lock:
            player = self.state.players.get(user_id)
            if player is None:
                return False
            if seq <= player.input_seq:
                return True
            player.input_seq = seq
            if not player.alive:
                player.move_x = 0
                player.move_y = 0
                player.shoot_requested = False
                player.mine_requested = False
                player.aim_x = aim_x
                player.aim_y = aim_y
                player.target_kind = None
                player.target_id = None
                return True
            player.move_x = move_x
            player.move_y = move_y
            player.aim_x = aim_x
            player.aim_y = aim_y
            if target_type is None or target_id is None:
                player.target_kind = None
                player.target_id = None
            elif target_type in {"player", "monster", "mine"}:
                player.target_kind = target_type
                player.target_id = int(target_id)
            else:
                player.target_kind = None
                player.target_id = None
            if shoot:
                player.shoot_requested = True
            if drop_mine:
                player.mine_requested = True
            return True

    async def request_mine_drop(self, user_id: int) -> bool:
        async with self.state.lock:
            player = self.state.players.get(user_id)
            if player is None:
                return False
            if not player.alive:
                return True
            player.mine_requested = True
            return True

    async def respawn(self, user_id: int) -> tuple[bool, str]:
        async with self.state.lock:
            player = self.state.players.get(user_id)
            if player is None:
                return False, "PLAYER_NOT_FOUND"
            if player.alive:
                return False, "PLAYER_ALREADY_ALIVE"
            if self.state.tick < player.dead_until_tick:
                return False, "RESPAWN_NOT_READY"
            game_settings = await self.game_config.get_settings("open_world")
            shield_points_max = max(0, int(game_settings["shield_points"]))
            invulnerability_seconds = max(1, int(game_settings["respawn_invulnerability_seconds"]))
            spawn_x, spawn_y = self._random_spawn_position()
            player.x = spawn_x
            player.y = spawn_y
            player.alive = True
            player.damage_taken = 0
            player.shield_points = shield_points_max
            player.last_damage_tick = self.state.tick
            player.last_shield_regen_tick = self.state.tick
            player.invulnerable_until_tick = self.state.tick + (invulnerability_seconds * self.tick_rate)
            player.dead_until_tick = 0
            player.move_x = 0
            player.move_y = 0
            player.shoot_requested = False
            player.mine_requested = False
            player.target_kind = None
            player.target_id = None
            await self.connection_manager.send_json(
                self.connection_manager.connections_by_user.get(user_id),
                "open_world_respawned",
                {"invulnerable_seconds": invulnerability_seconds},
            )
            return True, "OK"

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(self.tick_interval)
            async with self.state.lock:
                self.state.tick += 1
                await self._tick()
                await self.connection_manager.broadcast_open_world_state(self.state, self.tick_rate)

    async def _tick(self) -> None:
        game_settings = await self.game_config.get_settings("open_world")
        self.monster_collision_radius = max(0.1, float(game_settings["monster_hitbox_radius"]))
        await self._sync_monsters_population(game_settings)
        await self._apply_shield_regen(game_settings)
        await self._apply_inputs(game_settings)
        await self._advance_monsters(game_settings)
        await self._advance_mines(game_settings)
        await self._advance_projectiles(game_settings)

    async def _sync_monsters_population(self, game_settings: dict[str, float]) -> None:
        max_alive = max(0, int(game_settings["monster_max_alive"]))
        monster_life = max(1, int(game_settings["monster_life"]))

        self.state.pending_monster_respawns = sorted(self.state.pending_monster_respawns)
        while self.state.pending_monster_respawns and self.state.pending_monster_respawns[0] <= self.state.tick:
            if len(self.state.monsters) >= max_alive:
                break
            self.state.pending_monster_respawns.pop(0)
            self._spawn_monster(monster_life)

        total_reserved = len(self.state.monsters) + len(self.state.pending_monster_respawns)
        while total_reserved < max_alive:
            self._spawn_monster(monster_life)
            total_reserved = len(self.state.monsters) + len(self.state.pending_monster_respawns)

        while len(self.state.monsters) > max_alive:
            monster_id = next(iter(self.state.monsters.keys()))
            self.state.monsters.pop(monster_id, None)

        while len(self.state.monsters) + len(self.state.pending_monster_respawns) > max_alive:
            if not self.state.pending_monster_respawns:
                break
            self.state.pending_monster_respawns.pop()

    def _spawn_monster(self, monster_life: int) -> None:
        x, y = self._random_monster_spawn_position()
        target_x, target_y = self._random_walk_target()
        monster = OpenWorldMonster(
            monster_id=self.state.next_monster_id,
            x=x,
            y=y,
            aim_x=target_x,
            aim_y=target_y,
            hp=monster_life,
            max_hp=monster_life,
            move_target_x=target_x,
            move_target_y=target_y,
            last_shot_tick=self.state.tick,
            last_retarget_tick=self.state.tick,
        )
        self.state.monsters[monster.monster_id] = monster
        self.state.next_monster_id += 1

    async def _apply_inputs(self, game_settings: dict[str, float]) -> None:
        movement_speed = game_settings["movement_speed"] * self.visual_speed_factor
        fire_cooldown_ticks = max(1, int(game_settings["fire_cooldown_ticks"]))
        attack_range = max(0.1, float(game_settings["attack_range"]))
        mine_cooldown_ticks = max(1, int(game_settings["mine_cooldown_ticks"]))
        mine_max_active_per_player = max(1, int(game_settings["mine_max_active_per_player"]))
        shield_points_max = max(0, int(game_settings["shield_points"]))
        projectile_speed = float(game_settings["projectile_speed"]) * self.visual_speed_factor
        border_padding = max(
            self.player_collision_radius,
            float(game_settings["player_hitbox_radius"]) * self.visual_x_axis_factor,
        )

        for player in self.state.players.values():
            self._sync_shield_state(player, shield_points_max, self.state.tick)
            if not player.alive:
                continue
            locked_target = self._resolve_locked_target(player)

            input_x = float(player.move_x)
            input_y = float(player.move_y)
            input_magnitude = math.hypot(input_x, input_y)
            if input_magnitude > 0.0:
                input_x /= input_magnitude
                input_y /= input_magnitude

            move_x = input_x * self.visual_x_axis_factor
            move_y = input_y

            next_x = max(border_padding, min(100.0 - border_padding, player.x + (move_x * movement_speed)))
            if not self._collides_with_obstacle(next_x, player.y, self.player_collision_radius):
                player.x = next_x

            next_y = max(border_padding, min(100.0 - border_padding, player.y + (move_y * movement_speed)))
            if not self._collides_with_obstacle(player.x, next_y, self.player_collision_radius):
                player.y = next_y

            attacking_target = player.shoot_requested and locked_target is not None and self.state.tick >= player.invulnerable_until_tick
            if attacking_target:
                player.aim_x = locked_target[0]
                player.aim_y = locked_target[1]
            elif input_magnitude > 0.0:
                player.aim_x = max(0.0, min(100.0, player.x + (move_x * 12.0)))
                player.aim_y = max(0.0, min(100.0, player.y + (move_y * 12.0)))

            if player.shoot_requested:
                player.shoot_requested = False
                can_shoot = self.state.tick >= player.invulnerable_until_tick
                if can_shoot and (self.state.tick - player.last_shot_tick) >= fire_cooldown_ticks:
                    if locked_target is None:
                        continue
                    target_x, target_y, target_kind, target_entity_id = locked_target
                    target_distance = self._visual_distance(player.x, player.y, target_x, target_y)
                    target_click_radius = self._target_click_radius(game_settings, target_kind)
                    target_distance = max(0.0, target_distance - target_click_radius)
                    if target_distance > attack_range:
                        continue
                    delta_x = target_x - player.x
                    delta_y = target_y - player.y
                    distance = math.hypot(delta_x, delta_y) or 1.0
                    player.last_shot_tick = self.state.tick
                    self.state.projectiles.append(
                        Projectile(
                            projectile_id=self.state.next_projectile_id,
                            owner_user_id=player.user_id,
                            x=player.x,
                            y=player.y,
                            velocity_x=(delta_x / distance) * projectile_speed,
                            velocity_y=(delta_y / distance) * projectile_speed,
                            speed=projectile_speed,
                            owner_kind="player",
                            owner_entity_id=player.user_id,
                            target_kind=target_kind,
                            target_entity_id=target_entity_id,
                        )
                    )
                    self.state.next_projectile_id += 1

            if player.mine_requested:
                player.mine_requested = False
                if (self.state.tick - player.last_mine_tick) >= mine_cooldown_ticks:
                    owned_mines = sum(1 for mine in self.state.mines if mine.owner_user_id == player.user_id)
                    if owned_mines >= mine_max_active_per_player:
                        continue
                    player.last_mine_tick = self.state.tick
                    self.state.mines.append(
                        Mine(
                            mine_id=self.state.next_mine_id,
                            owner_user_id=player.user_id,
                            x=player.x,
                            y=player.y,
                            created_tick=self.state.tick,
                        )
                    )
                    self.state.next_mine_id += 1

    async def _advance_monsters(self, game_settings: dict[str, float]) -> None:
        if not self.state.monsters:
            return
        monster_speed = float(game_settings["monster_move_speed"]) * self.visual_speed_factor
        fire_cooldown_ticks = max(1, int(game_settings["monster_fire_cooldown_ticks"]))
        projectile_speed = float(game_settings["monster_projectile_speed"]) * self.visual_speed_factor

        for monster in self.state.monsters.values():
            if (self.state.tick - monster.last_retarget_tick) >= self.tick_rate * 3 or self._visual_distance(
                monster.x, monster.y, monster.move_target_x, monster.move_target_y
            ) <= 1.2:
                monster.move_target_x, monster.move_target_y = self._random_walk_target()
                monster.last_retarget_tick = self.state.tick

            delta_target_x = monster.move_target_x - monster.x
            delta_target_y = monster.move_target_y - monster.y
            distance_to_target = math.hypot(delta_target_x, delta_target_y) or 1.0
            step_x = (delta_target_x / distance_to_target) * monster_speed * self.visual_x_axis_factor
            step_y = (delta_target_y / distance_to_target) * monster_speed

            next_x = max(0.0, min(100.0, monster.x + step_x))
            if not self._collides_with_obstacle(next_x, monster.y, self.monster_collision_radius):
                monster.x = next_x
            next_y = max(0.0, min(100.0, monster.y + step_y))
            if not self._collides_with_obstacle(monster.x, next_y, self.monster_collision_radius):
                monster.y = next_y

            target_player = self._nearest_alive_player(monster.x, monster.y)
            if target_player is not None:
                monster.aim_x = target_player.x
                monster.aim_y = target_player.y
                if (self.state.tick - monster.last_shot_tick) >= fire_cooldown_ticks:
                    dx = target_player.x - monster.x
                    dy = target_player.y - monster.y
                    distance = math.hypot(dx, dy) or 1.0
                    monster.last_shot_tick = self.state.tick
                    self.state.projectiles.append(
                        Projectile(
                            projectile_id=self.state.next_projectile_id,
                            owner_user_id=0,
                            x=monster.x,
                            y=monster.y,
                            velocity_x=(dx / distance) * projectile_speed,
                            velocity_y=(dy / distance) * projectile_speed,
                            speed=projectile_speed,
                            owner_kind="monster",
                            owner_entity_id=monster.monster_id,
                        )
                    )
                    self.state.next_projectile_id += 1

    async def _advance_mines(self, game_settings: dict[str, float]) -> None:
        hits_to_win = max(1, int(game_settings["hits_to_win"]))
        shield_points_max = max(0, int(game_settings["shield_points"]))
        player_hitbox_radius = game_settings["player_hitbox_radius"]
        mine_hitbox_radius = game_settings["mine_hitbox_radius"]
        hit_distance = player_hitbox_radius + mine_hitbox_radius
        visible_to_all_ticks = self.tick_rate * 2

        active: list[Mine] = []
        for mine in self.state.mines:
            if (self.state.tick - mine.created_tick) < visible_to_all_ticks:
                active.append(mine)
                continue

            target = self._find_target_player(
                mine.x,
                mine.y,
                hit_distance,
                owner_user_id=mine.owner_user_id,
            )
            if target is None:
                active.append(mine)
                continue

            attacker = self.state.players.get(mine.owner_user_id)
            life_damage_applied = self._apply_hit_damage(target, shield_points_max, self.state.tick)
            await self.connection_manager.broadcast_open_world_hit(
                self.state,
                attacker_id=mine.owner_user_id,
                target_id=target.user_id,
                source="mine",
                shield_blocked=not life_damage_applied,
                attacker_kind="player" if attacker is not None else "neutral",
                attacker_monster_id=None,
            )
            if life_damage_applied and target.damage_taken >= hits_to_win:
                if attacker is not None:
                    await self._kill_player(attacker, target)
                else:
                    target.deaths += 1
                    target.alive = False
                    target.damage_taken = 0
                    target.shield_points = 0
                    target.last_damage_tick = self.state.tick
                    target.last_shield_regen_tick = self.state.tick
                    target.dead_until_tick = self.state.tick + (3 * self.tick_rate)
                    target.invulnerable_until_tick = 0
                    target.move_x = 0
                    target.move_y = 0
                    target.shoot_requested = False
                    target.mine_requested = False
                    target.target_kind = None
                    target.target_id = None
                    await self.connection_manager.broadcast_open_world_death(
                        self.state,
                        target_id=target.user_id,
                        killer_id=mine.owner_user_id,
                        respawn_seconds=3,
                    )

        self.state.mines = active

    async def _advance_projectiles(self, game_settings: dict[str, float]) -> None:
        hits_to_win = max(1, int(game_settings["hits_to_win"]))
        mine_hits_to_destroy = max(1, int(game_settings["mine_hits_to_destroy"]))
        shield_points_max = max(0, int(game_settings["shield_points"]))
        monster_respawn_ticks = max(1, int(game_settings["monster_respawn_seconds"]) * self.tick_rate)
        player_hitbox_radius = game_settings["player_hitbox_radius"]
        projectile_hitbox_radius = game_settings["projectile_hitbox_radius"]
        mine_hitbox_radius = game_settings["mine_hitbox_radius"]
        hit_distance = player_hitbox_radius + projectile_hitbox_radius
        mine_hit_distance = mine_hitbox_radius + projectile_hitbox_radius
        monster_hit_distance = self.monster_collision_radius + projectile_hitbox_radius

        active: list[Projectile] = []
        for projectile in self.state.projectiles:
            if projectile.owner_kind == "player" and projectile.target_kind in {"player", "monster", "mine"}:
                target_position = self._resolve_projectile_target(projectile)
                if target_position is None:
                    continue
                target_x, target_y = target_position
                delta_target_x = target_x - projectile.x
                delta_target_y = target_y - projectile.y
                distance_to_target = math.hypot(delta_target_x, delta_target_y) or 1.0
                projectile.velocity_x = (delta_target_x / distance_to_target) * projectile.speed
                projectile.velocity_y = (delta_target_y / distance_to_target) * projectile.speed

            previous_x = projectile.x
            previous_y = projectile.y
            projectile.x += projectile.velocity_x
            projectile.y += projectile.velocity_y
            if projectile.x < 0 or projectile.x > 100 or projectile.y < 0 or projectile.y > 100:
                continue
            if self._collides_with_obstacle_visual(projectile.x, projectile.y, projectile_hitbox_radius):
                continue

            if projectile.owner_kind == "player":
                expected_mine_id = projectile.target_entity_id if projectile.target_kind == "mine" else None
                enemy_mine_hit = next(
                    (
                        mine
                        for mine in self.state.mines
                        if mine.owner_user_id != projectile.owner_user_id
                        and (expected_mine_id is None or mine.mine_id == expected_mine_id)
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
                    if mine_destroyed:
                        self.state.mines = [
                            mine for mine in self.state.mines if mine.mine_id != enemy_mine_hit.mine_id
                        ]
                    await self.connection_manager.broadcast_open_world_mine_hit(
                        self.state,
                        attacker_id=projectile.owner_user_id,
                        mine_owner_id=enemy_mine_hit.owner_user_id,
                        mine_id=enemy_mine_hit.mine_id,
                        destroyed=mine_destroyed,
                    )
                    continue

                if projectile.target_kind != "mine":
                    hit_monster = self._find_hit_monster(
                        projectile.x,
                        projectile.y,
                        monster_hit_distance,
                        expected_monster_id=projectile.target_entity_id if projectile.target_kind == "monster" else None,
                    )
                    if hit_monster is not None:
                        hit_monster.hp = max(0, hit_monster.hp - 1)
                        destroyed = hit_monster.hp <= 0
                        await self.connection_manager.broadcast_open_world_monster_hit(
                            self.state,
                            monster_id=hit_monster.monster_id,
                            hp=hit_monster.hp,
                            max_hp=hit_monster.max_hp,
                            destroyed=destroyed,
                            x=hit_monster.x,
                            y=hit_monster.y,
                        )
                        if destroyed:
                            self.state.monsters.pop(hit_monster.monster_id, None)
                            self.state.pending_monster_respawns.append(self.state.tick + monster_respawn_ticks)
                        continue

                if projectile.target_kind != "mine":
                    target = self._find_target_player(
                        projectile.x,
                        projectile.y,
                        hit_distance,
                        owner_user_id=projectile.owner_user_id,
                        expected_target_id=projectile.target_entity_id if projectile.target_kind == "player" else None,
                    )
                    if target is None:
                        active.append(projectile)
                        continue

                    attacker = self.state.players.get(projectile.owner_user_id)
                    life_damage_applied = self._apply_hit_damage(target, shield_points_max, self.state.tick)
                    await self.connection_manager.broadcast_open_world_hit(
                        self.state,
                        attacker_id=projectile.owner_user_id,
                        target_id=target.user_id,
                        source="projectile",
                        shield_blocked=not life_damage_applied,
                        attacker_kind="player" if attacker is not None else "neutral",
                        attacker_monster_id=None,
                    )
                    if life_damage_applied and target.damage_taken >= hits_to_win:
                        if attacker is not None:
                            await self._kill_player(attacker, target)
                        else:
                            target.deaths += 1
                            target.alive = False
                            target.damage_taken = 0
                            target.shield_points = 0
                            target.last_damage_tick = self.state.tick
                            target.last_shield_regen_tick = self.state.tick
                            target.dead_until_tick = self.state.tick + (3 * self.tick_rate)
                            target.invulnerable_until_tick = 0
                            target.move_x = 0
                            target.move_y = 0
                            target.shoot_requested = False
                            target.mine_requested = False
                            target.target_kind = None
                            target.target_id = None
                            await self.connection_manager.broadcast_open_world_death(
                                self.state,
                                target_id=target.user_id,
                                killer_id=projectile.owner_user_id,
                                respawn_seconds=3,
                            )
                    continue
                active.append(projectile)
                continue

            if projectile.owner_kind == "monster":
                target = self._find_target_player_for_monster(projectile.x, projectile.y, hit_distance)
                if target is None:
                    active.append(projectile)
                    continue
                life_damage_applied = self._apply_hit_damage(target, shield_points_max, self.state.tick)
                await self.connection_manager.broadcast_open_world_hit(
                    self.state,
                    attacker_id=0,
                    target_id=target.user_id,
                    source="monster_projectile",
                    shield_blocked=not life_damage_applied,
                    attacker_kind="monster",
                    attacker_monster_id=projectile.owner_entity_id,
                )
                if life_damage_applied and target.damage_taken >= hits_to_win:
                    target.deaths += 1
                    target.alive = False
                    target.damage_taken = 0
                    target.shield_points = 0
                    target.last_damage_tick = self.state.tick
                    target.last_shield_regen_tick = self.state.tick
                    target.dead_until_tick = self.state.tick + (3 * self.tick_rate)
                    target.invulnerable_until_tick = 0
                    target.move_x = 0
                    target.move_y = 0
                    target.shoot_requested = False
                    target.mine_requested = False
                    target.target_kind = None
                    target.target_id = None
                    await self.connection_manager.broadcast_open_world_death(
                        self.state,
                        target_id=target.user_id,
                        killer_id=0,
                        respawn_seconds=3,
                    )
                continue

            active.append(projectile)

        self.state.projectiles = active

    async def _apply_shield_regen(self, game_settings: dict[str, float]) -> None:
        shield_points_max = max(0, int(game_settings["shield_points"]))
        shield_regen_ticks = max(1, int(game_settings["shield_regen_seconds"]) * self.tick_rate)
        for player in self.state.players.values():
            self._sync_shield_state(player, shield_points_max, self.state.tick)
            if not player.alive:
                continue
            if player.invulnerable_until_tick > self.state.tick:
                continue
            if player.shield_points >= shield_points_max:
                continue
            ticks_since_damage = max(0, self.state.tick - player.last_damage_tick)
            if ticks_since_damage < shield_regen_ticks:
                continue
            regen_cycles = (ticks_since_damage - shield_regen_ticks) // shield_regen_ticks
            regen_tick = player.last_damage_tick + shield_regen_ticks + (regen_cycles * shield_regen_ticks)
            if regen_tick <= player.last_shield_regen_tick:
                continue
            player.shield_points = min(shield_points_max, player.shield_points + 1)
            player.last_shield_regen_tick = regen_tick

    async def _kill_player(self, attacker: OpenWorldPlayer, target: OpenWorldPlayer) -> None:
        attacker.kills += 1
        target.deaths += 1
        target.alive = False
        target.damage_taken = 0
        target.shield_points = 0
        target.last_damage_tick = self.state.tick
        target.last_shield_regen_tick = self.state.tick
        target.dead_until_tick = self.state.tick + (3 * self.tick_rate)
        target.invulnerable_until_tick = 0
        target.move_x = 0
        target.move_y = 0
        target.shoot_requested = False
        target.mine_requested = False
        target.target_kind = None
        target.target_id = None
        await self.connection_manager.broadcast_open_world_death(
            self.state,
            target_id=target.user_id,
            killer_id=attacker.user_id,
            respawn_seconds=3,
        )

    def _find_target_player(
        self,
        x: float,
        y: float,
        hit_distance: float,
        owner_user_id: int,
        expected_target_id: int | None = None,
    ) -> OpenWorldPlayer | None:
        closest: OpenWorldPlayer | None = None
        closest_distance = float("inf")
        for player in self.state.players.values():
            if player.user_id == owner_user_id:
                continue
            if expected_target_id is not None and player.user_id != expected_target_id:
                continue
            if not player.alive:
                continue
            if player.invulnerable_until_tick > self.state.tick:
                continue
            distance = self._visual_distance(x, y, player.x, player.y)
            if distance > hit_distance:
                continue
            if distance < closest_distance:
                closest_distance = distance
                closest = player
        return closest

    def _find_target_player_for_monster(self, x: float, y: float, hit_distance: float) -> OpenWorldPlayer | None:
        closest: OpenWorldPlayer | None = None
        closest_distance = float("inf")
        for player in self.state.players.values():
            if not player.alive:
                continue
            if player.invulnerable_until_tick > self.state.tick:
                continue
            distance = self._visual_distance(x, y, player.x, player.y)
            if distance > hit_distance:
                continue
            if distance < closest_distance:
                closest_distance = distance
                closest = player
        return closest

    def _nearest_alive_player(self, x: float, y: float) -> OpenWorldPlayer | None:
        closest: OpenWorldPlayer | None = None
        closest_distance = float("inf")
        for player in self.state.players.values():
            if not player.alive:
                continue
            distance = self._visual_distance(x, y, player.x, player.y)
            if distance < closest_distance:
                closest_distance = distance
                closest = player
        return closest

    def _find_hit_monster(
        self,
        x: float,
        y: float,
        hit_distance: float,
        expected_monster_id: int | None = None,
    ) -> OpenWorldMonster | None:
        closest: OpenWorldMonster | None = None
        closest_distance = float("inf")
        for monster in self.state.monsters.values():
            if expected_monster_id is not None and monster.monster_id != expected_monster_id:
                continue
            distance = self._visual_distance(x, y, monster.x, monster.y)
            if distance > hit_distance:
                continue
            if distance < closest_distance:
                closest_distance = distance
                closest = monster
        return closest

    def _resolve_locked_target(self, player: OpenWorldPlayer) -> tuple[float, float, str, int] | None:
        if player.target_kind not in {"player", "monster", "mine"} or player.target_id is None:
            player.target_kind = None
            player.target_id = None
            return None
        if player.target_kind == "player":
            target = self.state.players.get(player.target_id)
            if target is None or target.user_id == player.user_id or not target.alive:
                player.target_kind = None
                player.target_id = None
                return None
            if target.invulnerable_until_tick > self.state.tick:
                player.target_kind = None
                player.target_id = None
                return None
            return target.x, target.y, "player", target.user_id
        target_monster = self.state.monsters.get(player.target_id)
        if player.target_kind == "monster":
            if target_monster is None:
                player.target_kind = None
                player.target_id = None
                return None
            return target_monster.x, target_monster.y, "monster", target_monster.monster_id

        target_mine = next((mine for mine in self.state.mines if mine.mine_id == player.target_id), None)
        if target_mine is None:
            player.target_kind = None
            player.target_id = None
            return None
        if target_mine.owner_user_id == player.user_id:
            player.target_kind = None
            player.target_id = None
            return None
        return target_mine.x, target_mine.y, "mine", target_mine.mine_id

    def _resolve_projectile_target(self, projectile: Projectile) -> tuple[float, float] | None:
        if projectile.target_kind == "player":
            if projectile.target_entity_id is None:
                return None
            target_player = self.state.players.get(projectile.target_entity_id)
            if target_player is None or not target_player.alive:
                return None
            if target_player.invulnerable_until_tick > self.state.tick:
                return None
            return target_player.x, target_player.y
        if projectile.target_kind == "monster":
            if projectile.target_entity_id is None:
                return None
            target_monster = self.state.monsters.get(projectile.target_entity_id)
            if target_monster is None:
                return None
            return target_monster.x, target_monster.y
        if projectile.target_kind == "mine":
            if projectile.target_entity_id is None:
                return None
            target_mine = next((mine for mine in self.state.mines if mine.mine_id == projectile.target_entity_id), None)
            if target_mine is None:
                return None
            if target_mine.owner_user_id == projectile.owner_user_id:
                return None
            return target_mine.x, target_mine.y
        return None

    @staticmethod
    def _target_click_radius(game_settings: dict[str, float], target_kind: str) -> float:
        if target_kind == "player":
            player_hitbox_radius = float(game_settings["player_hitbox_radius"])
            return max(2.2, player_hitbox_radius + 0.8)
        if target_kind == "monster":
            monster_hitbox_radius = float(game_settings["monster_hitbox_radius"])
            return max(2.2, monster_hitbox_radius + 0.8)
        if target_kind == "mine":
            mine_hitbox_radius = float(game_settings["mine_hitbox_radius"])
            return max(1.8, mine_hitbox_radius + 0.8)
        return 0.0

    @staticmethod
    def _sync_shield_state(player: OpenWorldPlayer, shield_points_max: int, current_tick: int) -> None:
        if shield_points_max <= 0:
            player.shield_points = 0
            player.last_shield_regen_tick = current_tick
            return
        player.shield_points = max(0, min(shield_points_max, int(player.shield_points)))
        player.last_damage_tick = max(0, int(player.last_damage_tick))
        player.last_shield_regen_tick = max(player.last_damage_tick, int(player.last_shield_regen_tick))

    @staticmethod
    def _apply_hit_damage(target: OpenWorldPlayer, shield_points_max: int, current_tick: int) -> bool:
        target.last_damage_tick = current_tick
        target.last_shield_regen_tick = current_tick
        if shield_points_max > 0 and target.shield_points > 0:
            target.shield_points = max(0, target.shield_points - 1)
            return False
        target.damage_taken += 1
        return True

    def _random_walk_target(self) -> tuple[float, float]:
        for _ in range(20):
            x = random.uniform(8.0, 92.0)
            y = random.uniform(8.0, 92.0)
            if self._collides_with_obstacle(x, y, self.monster_collision_radius):
                continue
            return x, y
        return 50.0, 50.0

    def _random_spawn_position(self) -> tuple[float, float]:
        for _ in range(50):
            x = random.uniform(8.0, 92.0)
            y = random.uniform(8.0, 92.0)
            if self._collides_with_obstacle(x, y, self.player_collision_radius):
                continue
            if any(player.alive and self._visual_distance(x, y, player.x, player.y) < 8.0 for player in self.state.players.values()):
                continue
            if any(self._visual_distance(x, y, monster.x, monster.y) < 8.0 for monster in self.state.monsters.values()):
                continue
            return x, y
        return 50.0, 50.0

    def _random_monster_spawn_position(self) -> tuple[float, float]:
        for _ in range(50):
            x = random.uniform(8.0, 92.0)
            y = random.uniform(8.0, 92.0)
            if self._collides_with_obstacle(x, y, self.monster_collision_radius):
                continue
            if any(player.alive and self._visual_distance(x, y, player.x, player.y) < 10.0 for player in self.state.players.values()):
                continue
            if any(self._visual_distance(x, y, monster.x, monster.y) < 10.0 for monster in self.state.monsters.values()):
                continue
            return x, y
        return 50.0, 50.0

    def _collides_with_obstacle(self, x: float, y: float, radius: float) -> bool:
        for obstacle in self.state.obstacles:
            closest_x = max(obstacle.x, min(x, obstacle.x + obstacle.width))
            closest_y = max(obstacle.y, min(y, obstacle.y + obstacle.height))
            if math.hypot(x - closest_x, y - closest_y) <= radius:
                return True
        return False

    def _visual_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        dx = (x1 - x2) / self.visual_x_axis_factor
        dy = y1 - y2
        return math.hypot(dx, dy)

    def _collides_with_obstacle_visual(self, x: float, y: float, radius: float) -> bool:
        for obstacle in self.state.obstacles:
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
