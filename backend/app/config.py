"""Application configuration via pydantic-settings."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — values are read from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://finsight:finsight_dev@localhost:5432/finsight"
    database_url_sync: str = "postgresql://finsight:finsight_dev@localhost:5432/finsight"

    # Security
    secret_key: str = "dev_secret_key_change_in_production"

    # Single-local-user mode (until auth lands): all data belongs to this account.
    local_user_email: str = "owner@finsight.local"

    # CORS — accepts "http://a,http://b" or JSON '["http://a","http://b"]'
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                return json.loads(raw)
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return value

    # Logging
    log_level: str = "info"

    # Storage
    storage_path: str = "./storage"
    max_upload_size_mb: int = 50

    # AI / OpenAI
    ai_enabled: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()
