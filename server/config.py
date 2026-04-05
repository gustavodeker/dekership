from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "dekership")
    db_user: str = os.getenv("DB_USER", "root")
    db_pass: str = os.getenv("DB_PASS", "")
    ws_tick_rate: int = int(os.getenv("WS_TICK_RATE", "20"))
    reconnect_timeout_seconds: int = int(os.getenv("RECONNECT_TIMEOUT_SECONDS", "10"))
    input_rate_limit_per_second: int = int(os.getenv("INPUT_RATE_LIMIT_PER_SECOND", "30"))
    allowed_origin: str = os.getenv("WS_ALLOWED_ORIGIN", "*")


settings = Settings()
