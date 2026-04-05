from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PlayerInput:
    seq: int = 0
    move_x: int = 0
    shoot: bool = False


@dataclass
class PlayerState:
    x: float
    y: float
    shoot_cooldown_ticks: int = 0


@dataclass
class Projectile:
    owner_user_id: int
    x: float
    y: float
    direction: Literal[-1, 1]


@dataclass
class SimulationSnapshot:
    tick: int
    p1: dict[str, float]
    p2: dict[str, float]
    projectiles: list[dict[str, float | int]]
    score: dict[str, int]


@dataclass
class MatchSimulationState:
    tick: int = 0
    width: float = 100.0
    p_bottom: PlayerState = field(default_factory=lambda: PlayerState(x=50.0, y=90.0))
    p_top: PlayerState = field(default_factory=lambda: PlayerState(x=50.0, y=10.0))
    projectiles: list[Projectile] = field(default_factory=list)


class SimulationEngine:
    def __init__(self) -> None:
        self.player_speed = 2.5
        self.projectile_speed = 3.0
        self.shoot_cooldown_ticks = 6
        self.hit_distance_x = 6.0
        self.hit_distance_y = 5.0

    def step(
        self,
        state: MatchSimulationState,
        bottom_user_id: int,
        top_user_id: int,
        bottom_input: PlayerInput,
        top_input: PlayerInput,
    ) -> tuple[SimulationSnapshot, list[tuple[int, int]]]:
        state.tick += 1

        self._apply_input(state.p_bottom, bottom_input)
        self._apply_input(state.p_top, top_input)

        if bottom_input.shoot and state.p_bottom.shoot_cooldown_ticks == 0:
            state.projectiles.append(Projectile(owner_user_id=bottom_user_id, x=state.p_bottom.x, y=state.p_bottom.y - 3, direction=-1))
            state.p_bottom.shoot_cooldown_ticks = self.shoot_cooldown_ticks

        if top_input.shoot and state.p_top.shoot_cooldown_ticks == 0:
            state.projectiles.append(Projectile(owner_user_id=top_user_id, x=state.p_top.x, y=state.p_top.y + 3, direction=1))
            state.p_top.shoot_cooldown_ticks = self.shoot_cooldown_ticks

        if state.p_bottom.shoot_cooldown_ticks > 0:
            state.p_bottom.shoot_cooldown_ticks -= 1
        if state.p_top.shoot_cooldown_ticks > 0:
            state.p_top.shoot_cooldown_ticks -= 1

        hits: list[tuple[int, int]] = []
        alive_projectiles: list[Projectile] = []
        for projectile in state.projectiles:
            projectile.y += self.projectile_speed * projectile.direction
            if projectile.y < 0 or projectile.y > 100:
                continue

            target = state.p_top if projectile.owner_user_id == bottom_user_id else state.p_bottom
            target_user_id = top_user_id if projectile.owner_user_id == bottom_user_id else bottom_user_id
            if abs(projectile.x - target.x) <= self.hit_distance_x and abs(projectile.y - target.y) <= self.hit_distance_y:
                hits.append((projectile.owner_user_id, target_user_id))
                continue

            alive_projectiles.append(projectile)

        state.projectiles = alive_projectiles

        snapshot = SimulationSnapshot(
            tick=state.tick,
            p1={"x": state.p_bottom.x, "y": state.p_bottom.y},
            p2={"x": state.p_top.x, "y": state.p_top.y},
            projectiles=[{"owner_user_id": p.owner_user_id, "x": p.x, "y": p.y} for p in state.projectiles],
            score={"p1": 0, "p2": 0},
        )
        return snapshot, hits

    def _apply_input(self, player: PlayerState, player_input: PlayerInput) -> None:
        move_x = max(-1, min(1, player_input.move_x))
        player.x += self.player_speed * move_x
        player.x = max(0.0, min(100.0, player.x))