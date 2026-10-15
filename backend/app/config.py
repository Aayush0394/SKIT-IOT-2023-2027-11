"""Central configuration, read from environment variables (.env supported)."""
import os
from pathlib import Path


def _load_env_file():
    env = Path(__file__).resolve().parents[1] / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env_file()


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB = os.getenv("MONGO_DB", "inventory_logs")
    LOAN_DAYS = int(os.getenv("LOAN_DAYS", "7"))
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]


settings = Settings()
