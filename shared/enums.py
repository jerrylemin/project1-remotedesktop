from __future__ import annotations

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


class EnvelopeType(StrEnum):
    HEARTBEAT = "heartbeat"
    AUTH = "auth"
    SUBSCRIBE_MACHINE = "subscribe_machine"
    FRAME = "frame"
    COMMAND = "command"
    COMMAND_RESULT = "command_result"
    INPUT_EVENT = "input_event"
    FILE_DISPATCH = "file_dispatch"
    JOB_STATUS = "job_status"
    AUDIT_EVENT = "audit_event"
    ACK = "ack"
    ERROR = "error"


class ActorType(StrEnum):
    ADMIN = "admin"
    AGENT = "agent"
    SYSTEM = "system"


class MachineStatus(StrEnum):
    ONLINE = "online"
    STALE = "stale"
    OFFLINE = "offline"


class Permission(StrEnum):
    MACHINES_READ = "machines:read"
    MACHINES_CONTROL = "machines:control"
    FILES_UPLOAD = "files:upload"
    FILES_DOWNLOAD = "files:download"
    JOBS_RUN = "jobs:run"
    AUDIT_READ = "audit:read"
    ADMIN_MANAGE = "admin:manage"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "admin": {
        Permission.MACHINES_READ,
        Permission.MACHINES_CONTROL,
        Permission.FILES_UPLOAD,
        Permission.FILES_DOWNLOAD,
        Permission.JOBS_RUN,
        Permission.AUDIT_READ,
        Permission.ADMIN_MANAGE,
    },
    "teacher": {
        Permission.MACHINES_READ,
        Permission.MACHINES_CONTROL,
        Permission.FILES_UPLOAD,
        Permission.AUDIT_READ,
    },
    "auditor": {Permission.MACHINES_READ, Permission.AUDIT_READ},
}


AUDIT_EVENT_TYPES = {
    "admin_login",
    "admin_logout",
    "agent_enrolled",
    "agent_online",
    "agent_stale",
    "agent_offline",
    "machine_selected",
    "session_created",
    "control_claimed",
    "control_denied",
    "control_released",
    "screenshot_started",
    "screenshot_stopped",
    "applications_listed",
    "application_started",
    "application_stopped",
    "processes_listed",
    "process_stopped",
    "process_started",
    "keylogger_demo_started",
    "keylogger_demo_stopped",
    "file_uploaded_to_server",
    "file_dispatched_to_agent",
    "file_downloaded_from_agent",
    "sandbox_file_created",
    "sandbox_job_started",
    "sandbox_job_finished",
    "webcam_started",
    "webcam_stopped",
    "webcam_snapshot",
    "webcam_denied",
    "input_event_sent",
    "restart_requested",
    "shutdown_requested",
    "power_cancel_requested",
    "auth_failed",
    "acl_denied",
    "command_failed",
    "agent_auth_succeeded",
    "agent_auth_failed",
    "consent_requested",
    "consent_approved",
    "consent_denied",
    "consent_expired",
    "consent_missing",
    "consent_blocked",
}
