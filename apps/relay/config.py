from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class RelaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_url: str = "http://localhost:8000"
    secret_key: str = "telepc-dev-secret"
    heartbeat_timeout_seconds: int = 15
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def origin_set(self) -> set[str]:
        return {origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()}


@lru_cache
def get_relay_settings() -> RelaySettings:
    return RelaySettings()

