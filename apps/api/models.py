from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.db import Base
from shared.time_utils import utc_now


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users", lazy="selectin")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    permissions_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    users: Mapped[list[User]] = relationship(secondary="user_roles", back_populates="roles", lazy="selectin")


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255))
    os: Mapped[str] = mapped_column(String(255), default="unknown")
    username: Mapped[str] = mapped_column(String(255), default="unknown")
    status: Mapped[str] = mapped_column(String(32), default="offline")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    secret: Mapped["MachineSecret | None"] = relationship(back_populates="machine", uselist=False)


class MachineSecret(Base):
    __tablename__ = "machine_secrets"

    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), primary_key=True)
    secret_hash: Mapped[str] = mapped_column(String(255))
    machine: Mapped[Machine] = relationship(back_populates="secret")


class MachineGrant(Base):
    __tablename__ = "machine_grants"
    __table_args__ = (UniqueConstraint("user_id", "machine_id", name="uq_machine_grants_user_machine"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), index=True)
    can_view: Mapped[bool] = mapped_column(Boolean, default=False)
    can_control: Mapped[bool] = mapped_column(Boolean, default=False)
    can_file: Mapped[bool] = mapped_column(Boolean, default=False)
    can_webcam: Mapped[bool] = mapped_column(Boolean, default=False)
    can_power: Mapped[bool] = mapped_column(Boolean, default=False)
    can_audit: Mapped[bool] = mapped_column(Boolean, default=False)


class RelayNode(Base):
    __tablename__ = "relay_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(255), unique=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ControlSession(Base):
    __tablename__ = "control_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), index=True)
    controller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionParticipant(Base):
    __tablename__ = "session_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("control_sessions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    mime: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    stored_path: Mapped[str] = mapped_column(String(1024))
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SandboxFile(Base):
    __tablename__ = "sandbox_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.id"), index=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), index=True)
    job_id: Mapped[str] = mapped_column(String(64), index=True)
    sandbox_path: Mapped[str] = mapped_column(String(1024))


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), index=True)
    command: Mapped[str] = mapped_column(String(255))
    cwd: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout: Mapped[int] = mapped_column(Integer, default=30)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    summary: Mapped[str] = mapped_column(String(255))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class EnrollToken(Base):
    __tablename__ = "enroll_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConsentRequest(Base):
    __tablename__ = "consent_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    command_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.machine_id"), index=True)
    requested_by: Mapped[str] = mapped_column(String(80), index=True)
    command_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reason: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    decided_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class ConsentDecision(Base):
    __tablename__ = "consent_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consent_id: Mapped[str] = mapped_column(ForeignKey("consent_requests.id"), index=True)
    decision: Mapped[str] = mapped_column(String(32))
    decided_by: Mapped[str] = mapped_column(String(80))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConsentPolicy(Base):
    __tablename__ = "consent_policies"

    command_type: Mapped[str] = mapped_column(String(80), primary_key=True)
    requires_consent: Mapped[bool] = mapped_column(Boolean, default=True)
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=300)
