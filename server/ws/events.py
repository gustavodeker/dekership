from typing import Any, Literal

from pydantic import BaseModel, Field


ClientEventName = Literal["auth", "room_create", "room_list", "room_join", "player_input", "ping"]


class Envelope(BaseModel):
    event: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PlayerInputPayload(BaseModel):
    seq: int
    move_x: int = 0
    shoot: bool = False


class OutgoingEnvelope(BaseModel):
    event: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)