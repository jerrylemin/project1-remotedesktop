from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.config import get_settings
from apps.api.deps import require_machine_access, require_permission
from apps.api.models import ConsentRequest, ControlSession, User
from apps.api.schemas import (
    AgentEnrollIn,
    AgentEnrollOut,
    ApplicationActionIn,
    EnrollTokenOut,
    FileDispatchIn,
    FileGetIn,
    JobHistoryOut,
    KeyloggerSessionIn,
    KeyloggerStartIn,
    MachineCommandOut,
    MachineOut,
    PowerActionIn,
    ProcessStopIn,
    ProcessStartIn,
    RemoteFileListIn,
    SandboxFileOut,
    ScreenActionIn,
    WebcamActionIn,
)
from apps.api.services.audit import record_audit
from apps.api.services.consent import require_active_consent
from apps.api.services.file import get_artifact, list_sandbox_files, record_dispatch
from apps.api.routers.jobs import job_history_out
from apps.api.services.job import list_jobs_for_machine
from apps.api.services.machine import create_enroll_token, enroll_machine, get_machine, list_machines
from apps.agent.app_manager import ALLOWED_APPLICATIONS
from shared.enums import Permission

router = APIRouter(prefix="/api", tags=["machines"])

PROTECTED_PROCESS_NAMES = {"lsass.exe", "winlogon.exe", "csrss.exe", "services.exe", "system", "registry"}
POWER_ACTIONS = {"lock", "restart", "shutdown", "cancel"}
INLINE_FILE_LIMIT = 512 * 1024


async def active_controller_user_id(db: AsyncSession, machine_id: str) -> int | None:
    return await db.scalar(
        select(ControlSession.controller_user_id).where(
            ControlSession.machine_id == machine_id,
            ControlSession.ended_at.is_(None),
        )
    )


async def machine_out(db: AsyncSession, machine) -> MachineOut:
    return MachineOut(
        machine_id=machine.machine_id,
        hostname=machine.hostname,
        os=machine.os,
        username=machine.username,
        status=machine.status,
        last_seen=machine.last_seen,
        active_controller_user_id=await active_controller_user_id(db, machine.machine_id),
    )


def command_response(action: str, **payload) -> MachineCommandOut:
    return MachineCommandOut(status="accepted", command={"action": action, **payload})


async def require_machine_exists(db: AsyncSession, machine_id: str) -> None:
    if await get_machine(db, machine_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="machine not found")


async def require_consent_or_403(
    db: AsyncSession,
    machine_id: str,
    command_type: str,
    user: User,
    command_payload: dict | None = None,
) -> ConsentRequest:
    try:
        return await require_active_consent(db, machine_id, command_type, str(user.id), command_payload)
    except PermissionError as exc:
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/machines", response_model=list[MachineOut])
async def machines(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MACHINES_READ)),
) -> list[MachineOut]:
    return [await machine_out(db, machine) for machine in await list_machines(db)]


@router.get("/machines/{machine_id}", response_model=MachineOut)
async def machine_detail(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_READ)),
) -> MachineOut:
    machine = await get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="machine not found")
    await require_machine_access(db, user, machine_id, "view")
    return await machine_out(db, machine)


@router.get("/machines/{machine_id}/processes")
async def machine_processes(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    await record_audit(db, event_type="processes_listed", summary="Process list requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
    await db.commit()
    return command_response("list_processes")


@router.get("/machines/{machine_id}/applications")
async def machine_applications(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    await record_audit(db, event_type="applications_listed", summary="Application list requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
    await db.commit()
    return command_response("list_applications")


@router.post("/machines/{machine_id}/applications/start", response_model=MachineCommandOut)
async def start_application(
    machine_id: str,
    body: ApplicationActionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    app_key = body.name.strip().lower().removesuffix(".exe")
    if app_key not in ALLOWED_APPLICATIONS:
        await record_audit(
            db,
            event_type="acl_denied",
            summary=f"Start application denied: {body.name}",
            actor_type="admin",
            actor_user_id=user.id,
            machine_id=machine_id,
            metadata={"app_key": body.name, "reason": "not_in_whitelist"},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application not in whitelist")
    authorization = await require_consent_or_403(db, machine_id, "APPLICATION_START", user, {"name": body.name, "confirm": body.confirm})
    await record_audit(db, event_type="application_started", summary=f"Start application requested: {app_key}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"app_key": app_key})
    await db.commit()
    return command_response("start_application", app_key=app_key, name=app_key, confirm=body.confirm, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/applications/stop", response_model=MachineCommandOut)
async def stop_application(
    machine_id: str,
    body: ApplicationActionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    app_key = body.name.strip().lower().removesuffix(".exe")
    if app_key not in ALLOWED_APPLICATIONS:
        await record_audit(
            db,
            event_type="acl_denied",
            summary=f"Stop application denied: {body.name}",
            actor_type="admin",
            actor_user_id=user.id,
            machine_id=machine_id,
            metadata={"app_key": body.name, "reason": "not_in_whitelist"},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="application not in whitelist")
    authorization = await require_consent_or_403(db, machine_id, "APPLICATION_STOP", user, {"name": body.name, "confirm": body.confirm})
    await record_audit(db, event_type="application_stopped", summary=f"Stop application requested: {app_key}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"app_key": app_key, "confirm": body.confirm})
    await db.commit()
    return command_response("stop_application", name=app_key, confirm=body.confirm, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/processes/{pid}/stop", response_model=MachineCommandOut)
async def stop_process(
    machine_id: str,
    pid: int,
    body: ProcessStopIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    name = (body.name or "").lower()
    if name in PROTECTED_PROCESS_NAMES:
        await record_audit(db, event_type="acl_denied", summary=f"Protected process stop denied: {body.name}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"pid": pid, "process": body.name})
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="protected process cannot be stopped")
    authorization = await require_consent_or_403(db, machine_id, "PROCESS_KILL", user, {"pid": pid, "name": body.name, "confirm": body.confirm})
    await record_audit(db, event_type="process_stopped", summary=f"Stop process requested: {pid}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"pid": pid, "process": body.name, "confirm": body.confirm})
    await db.commit()
    return command_response("stop_process", pid=pid, name=body.name, confirm=body.confirm, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/processes/start", response_model=MachineCommandOut)
async def start_process(
    machine_id: str,
    body: ProcessStartIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    process_key = body.process_key.strip().lower()
    if process_key not in get_settings().allowed_process_starts:
        await record_audit(
            db,
            event_type="acl_denied",
            summary=f"Start process denied: {body.process_key}",
            actor_type="admin",
            actor_user_id=user.id,
            machine_id=machine_id,
            metadata={"process_key": body.process_key, "reason": "not_in_allowlist"},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="process_key not in allowlist")
    await record_audit(
        db,
        event_type="process_started",
        summary=f"Start process requested: {process_key}",
        actor_type="admin",
        actor_user_id=user.id,
        machine_id=machine_id,
        metadata={"process_key": process_key},
    )
    await db.commit()
    return command_response("start_process", process_key=process_key)


@router.post("/machines/{machine_id}/screen/start", response_model=MachineCommandOut)
async def screen_start(machine_id: str, body: ScreenActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    authorization = await require_consent_or_403(db, machine_id, "LIVE_SCREEN_START", user, body.model_dump())
    await record_audit(db, event_type="screenshot_started", summary=f"Screen {body.mode} requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"mode": body.mode, "consent": body.consent})
    await db.commit()
    return command_response("screen_start", mode=body.mode, consent=body.consent, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/screen/stop", response_model=MachineCommandOut)
async def screen_stop(machine_id: str, body: ScreenActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    authorization = await require_consent_or_403(db, machine_id, "LIVE_SCREEN_STOP", user, body.model_dump())
    await record_audit(db, event_type="screenshot_stopped", summary="Screen view stopped", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"mode": body.mode})
    await db.commit()
    return command_response("screen_stop", mode=body.mode, consent=body.consent, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/screen/capture", response_model=MachineCommandOut)
async def screen_capture(machine_id: str, body: ScreenActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    authorization = await require_consent_or_403(db, machine_id, "SCREENSHOT", user, body.model_dump())
    await record_audit(db, event_type="screenshot_started", summary="Screenshot capture requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"mode": "capture", "consent": body.consent})
    await db.commit()
    return command_response("capture_screen", consent=body.consent, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/webcam/start", response_model=MachineCommandOut)
async def webcam_start(machine_id: str, body: WebcamActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "webcam")
    authorization = await require_consent_or_403(db, machine_id, "WEBCAM_START", user, body.model_dump())
    if not body.consent:
        await record_audit(db, event_type="acl_denied", summary="Webcam start denied without consent", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webcam requires consent")
    if not body.device_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webcam device_id is required")
    await record_audit(db, event_type="webcam_started", summary="Webcam start requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"consent": body.consent, "device_id": body.device_id})
    await db.commit()
    return command_response("webcam", start=True, consent=True, device_id=body.device_id, _command_id=authorization.command_id)


@router.get("/machines/{machine_id}/webcam/devices", response_model=MachineCommandOut)
async def webcam_devices(machine_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "webcam")
    authorization = await require_consent_or_403(db, machine_id, "WEBCAM_ENUMERATE", user, {})
    await record_audit(db, event_type="webcam_devices_listed", summary="Webcam devices requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
    await db.commit()
    return command_response("webcam_devices", _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/webcam/stop", response_model=MachineCommandOut)
async def webcam_stop(machine_id: str, body: WebcamActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "webcam")
    authorization = await require_consent_or_403(db, machine_id, "WEBCAM_STOP", user, body.model_dump())
    if not body.consent:
        await record_audit(db, event_type="acl_denied", summary="Webcam stop denied without consent", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webcam stop requires consent")
    await record_audit(db, event_type="webcam_stopped", summary="Webcam stop requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"consent": body.consent})
    await db.commit()
    return command_response("webcam", start=False, consent=body.consent, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/webcam/snapshot", response_model=MachineCommandOut)
async def webcam_snapshot(machine_id: str, body: WebcamActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "webcam")
    authorization = await require_consent_or_403(db, machine_id, "WEBCAM_START", user, body.model_dump())
    if not body.consent:
        await record_audit(db, event_type="webcam_denied", summary="Webcam snapshot denied without consent", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webcam requires consent")
    await record_audit(db, event_type="webcam_snapshot", summary="Webcam snapshot requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"consent": body.consent})
    await db.commit()
    return command_response("webcam_snapshot", consent=True, device_id=body.device_id, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/keylogger/start", response_model=MachineCommandOut)
async def keylogger_start(
    machine_id: str,
    body: KeyloggerStartIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    if not body.session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="keylogger session_id is required")
    payload = body.model_dump()
    authorization = await require_consent_or_403(db, machine_id, "KEYLOGGER_START", user, payload)
    if not body.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="keylogger requires consent")
    await record_audit(db, event_type="keylogger_started", summary="Keylogger lab capture requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"session_id": body.session_id, "ttl_seconds": body.ttl_seconds})
    await db.commit()
    return command_response("keylogger_start", session_id=body.session_id, ttl_seconds=body.ttl_seconds, consent=True, requested_by=str(user.id), _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/keylogger/stop", response_model=MachineCommandOut)
async def keylogger_stop(
    machine_id: str,
    body: KeyloggerSessionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    payload = body.model_dump()
    authorization = await require_consent_or_403(db, machine_id, "KEYLOGGER_STOP", user, payload)
    await record_audit(db, event_type="keylogger_stopped", summary="Keylogger lab capture stop requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"session_id": body.session_id})
    await db.commit()
    return command_response("keylogger_stop", session_id=body.session_id, consent=body.consent, _command_id=authorization.command_id)


@router.get("/machines/{machine_id}/keylogger/{session_id}/events", response_model=MachineCommandOut)
async def keylogger_events(
    machine_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    await record_audit(db, event_type="keylogger_events_viewed", summary="Keylogger lab events requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"session_id": session_id})
    await db.commit()
    return command_response("keylogger_events", session_id=session_id)


@router.post("/machines/{machine_id}/keylogger/{session_id}/export", response_model=MachineCommandOut)
async def keylogger_export(
    machine_id: str,
    session_id: str,
    body: KeyloggerSessionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    if body.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_id mismatch")
    payload = body.model_dump()
    authorization = await require_consent_or_403(db, machine_id, "KEYLOGGER_EXPORT", user, payload)
    await record_audit(db, event_type="keylogger_exported", summary="Keylogger lab export requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"session_id": session_id})
    await db.commit()
    return command_response("keylogger_export", session_id=session_id, consent=body.consent, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/power", response_model=MachineCommandOut)
async def power_action(
    machine_id: str,
    body: PowerActionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "power")
    action = body.action.lower()
    if action not in POWER_ACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported power action")
    reason = body.reason.strip()
    if action in {"restart", "shutdown"} and len(reason) < 5:
        await record_audit(db, event_type="acl_denied", summary=f"Power {action} denied without confirmation or reason", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"action": action})
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="power action requires reason of at least 5 characters")
    if not body.confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="power action requires confirm")
    authorization = None
    if action in {"restart", "shutdown"}:
        authorization = await require_consent_or_403(db, machine_id, f"POWER_{action.upper()}", user, body.model_dump())
    if action == "lock" and not reason:
        reason = "lock workstation"
    if action == "cancel" and not reason:
        reason = "cancel scheduled power action"
    event_type = f"{action}_requested" if action in {"restart", "shutdown"} else "power_cancel_requested" if action == "cancel" else "power_requested"
    await record_audit(db, event_type=event_type, summary=f"Power action requested: {action}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"action": action, "reason": reason})
    await db.commit()
    return command_response("power", power_action=action, confirm=True, reason=reason, **({"_command_id": authorization.command_id} if authorization else {}))


@router.post("/machines/{machine_id}/file-dispatch", response_model=MachineCommandOut)
async def file_dispatch(
    machine_id: str,
    body: FileDispatchIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_UPLOAD)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "file")
    artifact = await get_artifact(db, body.artifact_id)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")
    job_id = str(uuid4())
    filename = Path(artifact.filename).name
    await record_dispatch(db, artifact.id, machine_id, job_id, f"{machine_id}/{job_id}/{filename}")
    payload = {"filename": filename, "sha256": artifact.sha256, "size": artifact.size, "job_id": job_id}
    data = Path(artifact.stored_path).read_bytes()
    if len(data) <= INLINE_FILE_LIMIT:
        payload["content_base64"] = base64.b64encode(data).decode()
    else:
        payload["download_url"] = f"/api/artifacts/{artifact.id}/download"
    await record_audit(db, event_type="file_dispatched_to_agent", summary="File dispatched to agent sandbox", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"artifact_id": artifact.id, "job_id": job_id})
    await db.commit()
    return command_response("file_put", **payload)


@router.post("/machines/{machine_id}/file-get", response_model=MachineCommandOut)
async def file_get(
    machine_id: str,
    body: FileGetIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "file")
    authorization = await require_consent_or_403(db, machine_id, "FILE_DOWNLOAD", user, body.model_dump())
    if body.path.startswith(("../", "..\\", "\\\\", "/", "C:", "c:")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="path traversal rejected")
    await record_audit(db, event_type="file_downloaded_from_agent", summary="Sandbox file download requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"path": body.path})
    await db.commit()
    return command_response("file_get", path=body.path, _command_id=authorization.command_id)


@router.get("/machines/{machine_id}/remote-files/folders", response_model=MachineCommandOut)
async def remote_file_folders(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "file")
    await record_audit(db, event_type="file_roots_listed", summary="Remote file whitelist folders requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
    await db.commit()
    return command_response("remote_files_roots")


@router.post("/machines/{machine_id}/remote-files/list", response_model=MachineCommandOut)
async def remote_file_list(
    machine_id: str,
    body: RemoteFileListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "file")
    authorization = await require_consent_or_403(db, machine_id, "FILE_LIST", user, body.model_dump())
    if not body.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file list requires consent")
    await record_audit(db, event_type="file_list_requested", summary="Remote whitelist folder listing requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"root_path": body.root_path, "relative_path": body.relative_path})
    await db.commit()
    return command_response("remote_files_list", root_path=body.root_path, relative_path=body.relative_path, consent=True, _command_id=authorization.command_id)


@router.post("/machines/{machine_id}/remote-files/download", response_model=MachineCommandOut)
async def remote_file_download(
    machine_id: str,
    body: RemoteFileListIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "file")
    authorization = await require_consent_or_403(db, machine_id, "FILE_DOWNLOAD", user, body.model_dump())
    if not body.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file download requires consent")
    await record_audit(db, event_type="file_download_requested", summary="Remote whitelist file download requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"root_path": body.root_path, "relative_path": body.relative_path})
    await db.commit()
    return command_response("remote_file_download", root_path=body.root_path, relative_path=body.relative_path, consent=True, _command_id=authorization.command_id)


@router.get("/machines/{machine_id}/sandbox/files", response_model=list[SandboxFileOut])
async def machine_sandbox_files(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> list[SandboxFileOut]:
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "file")
    rows = await list_sandbox_files(db, machine_id)
    return [
        SandboxFileOut(
            artifact_id=artifact.id,
            filename=artifact.filename,
            size=artifact.size,
            sha256=artifact.sha256,
            uploaded_at=artifact.created_at,
            machine_id=item.machine_id,
            job_id=item.job_id,
            sandbox_path=item.sandbox_path,
        )
        for item, artifact in rows
    ]


@router.get("/machines/{machine_id}/sandbox/jobs", response_model=list[JobHistoryOut])
async def machine_sandbox_jobs(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.JOBS_RUN)),
):
    await require_machine_exists(db, machine_id)
    await require_machine_access(db, user, machine_id, "control")
    return [job_history_out(job) for job in await list_jobs_for_machine(db, machine_id)]


@router.post("/enroll-tokens", response_model=EnrollTokenOut)
async def enroll_token(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.ADMIN_MANAGE)),
) -> EnrollTokenOut:
    token = await create_enroll_token(db, user.id)
    await db.commit()
    return EnrollTokenOut(enroll_token=token)


@router.post("/agents/enroll", response_model=AgentEnrollOut)
async def agent_enroll(body: AgentEnrollIn, db: AsyncSession = Depends(get_db)) -> AgentEnrollOut:
    enrolled = await enroll_machine(
        db,
        enroll_token=body.enroll_token,
        hostname=body.hostname,
        os_name=body.os,
        username=body.username,
    )
    if enrolled is None:
        await record_audit(db, event_type="auth_failed", summary="Invalid enroll token", actor_type="agent")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid enroll token")
    machine, secret = enrolled
    await record_audit(
        db,
        event_type="agent_enrolled",
        summary=f"{machine.hostname} enrolled",
        actor_type="agent",
        machine_id=machine.machine_id,
    )
    await db.commit()
    return AgentEnrollOut(machine_id=machine.machine_id, machine_secret=secret)
