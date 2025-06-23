from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import SettingsConfigDict

# automatically read .env-file as soon as the module is imported
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
    EMAIL_WEBHOOK_URL: str | None = os.getenv("EMAIL_WEBHOOK_URL")
    SUPPORT_WEBHOOK_URL: str | None = os.getenv("SUPPORT_WEBHOOK_URL")
    N8N_API_KEY: str | None = os.getenv("N8N_API_KEY")
    VOICE_WEBHOOK_SECRET: str | None = os.getenv("VOICE_WEBHOOK_SECRET")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()