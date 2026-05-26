from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ALLOWLIST = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "mspaint": "mspaint.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
}


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    relay_url: str = "ws://localhost:8001"
    api_url: str = "http://localhost:8000"
    machine_token: str = ""
    machine_id: str = "fake-machine-001"
    sandbox_root: Path = Path("./sandbox")
    require_consent: bool = True
    agent_mode: str = "fake"
    job_timeout_seconds: int = 30
    runner_allowlist: str = "python,powershell,pwsh,cmd"
    app_allowlist: str = ",".join(APP_ALLOWLIST)
    enable_real_input: bool = False
    enable_real_power: bool = False

    @property
    def runners(self) -> set[str]:
        return {item.strip().lower() for item in self.runner_allowlist.split(",") if item.strip()}

    @property
    def apps(self) -> set[str]:
        return {item.strip().lower() for item in self.app_allowlist.split(",") if item.strip()}


@lru_cache
def get_agent_settings() -> AgentSettings:
    settings = AgentSettings()
    settings.sandbox_root.mkdir(parents=True, exist_ok=True)
    return settings
