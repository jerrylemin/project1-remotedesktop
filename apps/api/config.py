from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./telepc.db"
    secret_key: str = "telepc-dev-secret-change-me-32-bytes-minimum"
    internal_api_secret: str = "telepc-internal-dev-secret-change-me"
    access_token_expire_minutes: int = 480
    ws_ticket_ttl_seconds: int = 30
    artifact_root: Path = Path("./artifacts")
    max_upload_size: int = 10 * 1024 * 1024
    allowed_upload_ext: str = ".txt,.csv,.json,.py,.ps1,.png,.jpg,.jpeg,.pdf,.zip"
    app_allowlist: str = "notepad,calc,python,pwsh,powershell,cmd,bash"
    process_start_allowlist: str = "notepad,calculator,vscode,browser"
    relay_url: str = "ws://localhost:8001"
    api_url: str = "http://localhost:8000"
    cookie_name: str = "telepc_session"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000"])

    @property
    def allowed_extensions(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_upload_ext.split(",") if item.strip()}

    @property
    def allowed_apps(self) -> set[str]:
        return {item.strip().lower() for item in self.app_allowlist.split(",") if item.strip()}

    @property
    def allowed_process_starts(self) -> set[str]:
        return {item.strip().lower() for item in self.process_start_allowlist.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.artifact_root.mkdir(parents=True, exist_ok=True)
    return settings
