"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(80), nullable=False), sa.Column("email", sa.String(255)), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("roles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(80), nullable=False, unique=True), sa.Column("permissions_json", sa.JSON(), nullable=False))
    op.create_table("user_roles", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True), sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True))
    op.create_table("machines", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("machine_id", sa.String(64), nullable=False, unique=True), sa.Column("hostname", sa.String(255), nullable=False), sa.Column("os", sa.String(255), nullable=False), sa.Column("username", sa.String(255), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("last_seen", sa.DateTime(timezone=True)))
    op.create_index("ix_machines_machine_id", "machines", ["machine_id"], unique=True)
    op.create_table("machine_secrets", sa.Column("machine_id", sa.String(64), sa.ForeignKey("machines.machine_id"), primary_key=True), sa.Column("secret_hash", sa.String(255), nullable=False))
    op.create_table("machine_grants", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("machine_id", sa.String(64), sa.ForeignKey("machines.machine_id"), nullable=False), sa.Column("can_view", sa.Boolean(), nullable=False), sa.Column("can_control", sa.Boolean(), nullable=False), sa.Column("can_file", sa.Boolean(), nullable=False), sa.Column("can_webcam", sa.Boolean(), nullable=False), sa.Column("can_power", sa.Boolean(), nullable=False), sa.Column("can_audit", sa.Boolean(), nullable=False), sa.UniqueConstraint("user_id", "machine_id", name="uq_machine_grants_user_machine"))
    op.create_table("relay_nodes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("url", sa.String(255), nullable=False, unique=True), sa.Column("last_heartbeat", sa.DateTime(timezone=True)))
    op.create_table("control_sessions", sa.Column("id", sa.String(64), primary_key=True), sa.Column("machine_id", sa.String(64), sa.ForeignKey("machines.machine_id"), nullable=False), sa.Column("controller_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True)))
    op.create_table("session_participants", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("session_id", sa.String(64), sa.ForeignKey("control_sessions.id"), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("role", sa.String(32), nullable=False))
    op.create_table("artifacts", sa.Column("id", sa.String(64), primary_key=True), sa.Column("filename", sa.String(255), nullable=False), sa.Column("size", sa.Integer(), nullable=False), sa.Column("sha256", sa.String(64), nullable=False), sa.Column("mime", sa.String(120), nullable=False), sa.Column("stored_path", sa.String(1024), nullable=False), sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("sandbox_files", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("artifact_id", sa.String(64), sa.ForeignKey("artifacts.id"), nullable=False), sa.Column("machine_id", sa.String(64), sa.ForeignKey("machines.machine_id"), nullable=False), sa.Column("job_id", sa.String(64), nullable=False), sa.Column("sandbox_path", sa.String(1024), nullable=False))
    op.create_table("jobs", sa.Column("id", sa.String(64), primary_key=True), sa.Column("machine_id", sa.String(64), sa.ForeignKey("machines.machine_id"), nullable=False), sa.Column("command", sa.String(255), nullable=False), sa.Column("cwd", sa.String(1024)), sa.Column("stdout", sa.Text(), nullable=False), sa.Column("stderr", sa.Text(), nullable=False), sa.Column("exit_code", sa.Integer()), sa.Column("timeout", sa.Integer(), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("finished_at", sa.DateTime(timezone=True)))
    op.create_table("audit_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("machine_id", sa.String(64)), sa.Column("session_id", sa.String(64)), sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("actor_type", sa.String(32), nullable=False), sa.Column("event_type", sa.String(80), nullable=False), sa.Column("summary", sa.String(255), nullable=False), sa.Column("metadata_json", sa.JSON(), nullable=False), sa.Column("ip_address", sa.String(64)), sa.Column("user_agent", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("enroll_tokens", sa.Column("id", sa.String(64), primary_key=True), sa.Column("token_hash", sa.String(255), nullable=False, unique=True), sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("used_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("consent_requests", sa.Column("id", sa.String(64), primary_key=True), sa.Column("command_id", sa.String(64)), sa.Column("machine_id", sa.String(64), sa.ForeignKey("machines.machine_id"), nullable=False), sa.Column("requested_by", sa.String(80), nullable=False), sa.Column("command_type", sa.String(80), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("reason", sa.String(255), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("decided_by", sa.String(80)), sa.Column("decided_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("consent_decisions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("consent_id", sa.String(64), sa.ForeignKey("consent_requests.id"), nullable=False), sa.Column("decision", sa.String(32), nullable=False), sa.Column("decided_by", sa.String(80), nullable=False), sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("consent_policies", sa.Column("command_type", sa.String(80), primary_key=True), sa.Column("requires_consent", sa.Boolean(), nullable=False), sa.Column("ttl_seconds", sa.Integer(), nullable=False))


def downgrade() -> None:
    for table in ["consent_policies", "consent_decisions", "consent_requests", "enroll_tokens", "audit_events", "jobs", "sandbox_files", "artifacts", "session_participants", "control_sessions", "relay_nodes", "machine_grants", "machine_secrets", "machines", "user_roles", "roles", "users"]:
        op.drop_table(table)

