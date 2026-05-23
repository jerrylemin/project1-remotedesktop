from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class MachineOut(BaseModel):
    machine_id: str
    hostname: str
    os: str
    username: str
    status: str
    last_seen: datetime | None


class EnrollTokenOut(BaseModel):
    enroll_token: str


class AgentEnrollIn(BaseModel):
    enroll_token: str
    hostname: str
    os: str = "unknown"
    username: str = "unknown"


class AgentEnrollOut(BaseModel):
    machine_id: str
    machine_secret: str


class SessionCreateIn(BaseModel):
    machine_id: str


class SessionOut(BaseModel):
    id: str
    machine_id: str
    controller_user_id: int
    started_at: datetime
    ended_at: datetime | None


class AuditOut(BaseModel):
    id: int
    machine_id: str | None
    session_id: str | None
    actor_type: str
    event_type: str
    summary: str
    metadata_json: dict[str, Any]
    created_at: datetime


class SandboxFileOut(BaseModel):
    artifact_id: str
    filename: str
    size: int
    sha256: str
    uploaded_at: datetime
    machine_id: str
    job_id: str
    sandbox_path: str
    dispatched_status: str = "dispatched"


class JobCreateIn(BaseModel):
    machine_id: str
    command: str
    cwd: str | None = None
    timeout: int = Field(default=30, ge=1, le=300)


class JobOut(BaseModel):
    id: str
    machine_id: str
    command: str
    cwd: str | None
    stdout: str
    stderr: str
    exit_code: int | None
    timeout: int
    started_at: datetime | None
    finished_at: datetime | None


class JobHistoryOut(JobOut):
    status: str
    duration_seconds: float | None
    stdout_preview: str
    stderr_preview: str
