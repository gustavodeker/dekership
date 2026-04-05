from __future__ import annotations

from typing import Any


def make_event(event: str, payload: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
    return {
        "event": event,
        "request_id": request_id,
        "payload": payload,
    }
