from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic

from fastapi import WebSocket


@dataclass
class ConnectionCtx:
    websocket: WebSocket
    user_id: int | None = None
    username: str | None = None


class ConnectionManager:
    def __init__(self) -> None:
        self._ctx_by_ws: dict[WebSocket, ConnectionCtx] = {}
        self._ws_by_user: dict[int, WebSocket] = {}
        self._input_windows: dict[WebSocket, deque[float]] = defaultdict(deque)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._ctx_by_ws[websocket] = ConnectionCtx(websocket=websocket)

    def register_identity(self, websocket: WebSocket, user_id: int, username: str) -> None:
        ctx = self._ctx_by_ws[websocket]
        ctx.user_id = user_id
        ctx.username = username
        self._ws_by_user[user_id] = websocket

    def get_ctx(self, websocket: WebSocket) -> ConnectionCtx | None:
        return self._ctx_by_ws.get(websocket)

    def get_websocket_by_user(self, user_id: int) -> WebSocket | None:
        return self._ws_by_user.get(user_id)

    def allow_input(self, websocket: WebSocket, max_per_second: int) -> bool:
        now = monotonic()
        window = self._input_windows[websocket]
        while window and now - window[0] > 1.0:
            window.popleft()
        if len(window) >= max_per_second:
            return False
        window.append(now)
        return True

    def disconnect(self, websocket: WebSocket) -> ConnectionCtx | None:
        ctx = self._ctx_by_ws.pop(websocket, None)
        self._input_windows.pop(websocket, None)
        if ctx and ctx.user_id is not None and self._ws_by_user.get(ctx.user_id) is websocket:
            self._ws_by_user.pop(ctx.user_id, None)
        return ctx