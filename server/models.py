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
    shoot: bool = False


class RoomCreatePayload(BaseModel):
    room_name: str = Field(min_length=1, max_length=80)


class RoomJoinPayload(BaseModel):
    room_id: str = Field(min_length=36, max_length=36)


class AuthPayload(BaseModel):
    token: str = Field(min_length=1, max_length=255)
