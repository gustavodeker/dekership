from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Envelope(BaseModel):
    event: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PlayerInputPayload(BaseModel):
    seq: int = Field(ge=0)
    move_x: int = Field(ge=-1, le=1)
    move_y: int = Field(ge=-1, le=1)
    aim_x: float = Field(ge=0, le=100)
    aim_y: float = Field(ge=0, le=100)
    shoot: bool = False
    drop_mine: bool = False
    target_type: str | None = Field(default=None, pattern="^(player|monster)$")
    target_id: int | None = Field(default=None, ge=1)


class RoomCreatePayload(BaseModel):
    room_name: str = Field(min_length=1, max_length=80)


class RoomJoinPayload(BaseModel):
    room_id: str = Field(min_length=36, max_length=36)


class AuthPayload(BaseModel):
    token: str = Field(min_length=1, max_length=255)
