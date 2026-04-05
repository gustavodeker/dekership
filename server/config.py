from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "dekership")
    db_user: str = os.getenv("DB_USER", "root")
    db_pass: str = os.getenv("DB_PASS", "")
    ws_url: str = os.getenv("WS_URL", "ws://127.0.0.1:8765/ws")
    ws_allowed_origin: str = os.getenv("WS_ALLOWED_ORIGIN", "*")
    ws_tick_rate: int = int(os.getenv("WS_TICK_RATE", "20"))
    reconnect_timeout_seconds: int = int(os.getenv("RECONNECT_TIMEOUT_SECONDS", "10"))
    input_rate_limit_per_second: int = int(os.getenv("INPUT_RATE_LIMIT_PER_SECOND", "30"))
    auth_user_table: str = os.getenv("AUTH_USER_TABLE", "usuario")
    auth_id_column: str = os.getenv("AUTH_ID_COLUMN", "id")
    auth_username_column: str = os.getenv("AUTH_USERNAME_COLUMN", "usuario")
    auth_display_column: str = os.getenv("AUTH_DISPLAY_COLUMN", "usuario")
    auth_password_column: str = os.getenv("AUTH_PASSWORD_COLUMN", "senha")
    auth_token_column: str = os.getenv("AUTH_TOKEN_COLUMN", "token")
    default_admin_username: str = os.getenv("DEFAULT_ADMIN_USERNAME", "deker")


settings = Settings()
