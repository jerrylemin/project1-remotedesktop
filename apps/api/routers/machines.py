from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import get_current_user, require_permission
from apps.api.models import ControlSession, User
from apps.api.schemas import (
    AgentEnrollIn,
    AgentEnrollOut,
    ApplicationActionIn,
    EnrollTokenOut,
    FileDispatchIn,
    FileGetIn,
    JobHistoryOut,
    MachineCommandOut,
    MachineOut,
    PowerActionIn,
    ProcessStopIn,
    SandboxFileOut,
    ScreenActionIn,
    WebcamActionIn,
)
from apps.api.services.audit import record_audit
from apps.api.services.file import get_artifact, list_sandbox_files, record_dispatch
from apps.api.routers.jobs import job_history_out
from apps.api.services.job import list_jobs_for_machine
from apps.api.services.machine import create_enroll_token, enroll_machine, get_machine, list_machines
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
    _: User = Depends(require_permission(Permission.MACHINES_READ)),
) -> MachineOut:
    machine = await get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="machine not found")
    return await machine_out(db, machine)


@router.get("/machines/{machine_id}/processes")
async def machine_processes(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
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
    command = body.command or body.name
    await record_audit(db, event_type="application_started", summary=f"Start application requested: {body.name}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"name": body.name, "command": command})
    await db.commit()
    return command_response("start_application", command=command, name=body.name, confirm=body.confirm)


@router.post("/machines/{machine_id}/applications/stop", response_model=MachineCommandOut)
async def stop_application(
    machine_id: str,
    body: ApplicationActionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await record_audit(db, event_type="application_stopped", summary=f"Stop application requested: {body.name}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"name": body.name, "confirm": body.confirm})
    await db.commit()
    return command_response("stop_application", name=body.name, confirm=body.confirm)


@router.post("/machines/{machine_id}/processes/{pid}/stop", response_model=MachineCommandOut)
async def stop_process(
    machine_id: str,
    pid: int,
    body: ProcessStopIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    name = (body.name or "").lower()
    if name in PROTECTED_PROCESS_NAMES:
        await record_audit(db, event_type="acl_denied", summary=f"Protected process stop denied: {body.name}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"pid": pid, "process": body.name})
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="protected process cannot be stopped")
    await record_audit(db, event_type="process_stopped", summary=f"Stop process requested: {pid}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"pid": pid, "process": body.name, "confirm": body.confirm})
    await db.commit()
    return command_response("stop_process", pid=pid, name=body.name, confirm=body.confirm)


@router.post("/machines/{machine_id}/screen/start", response_model=MachineCommandOut)
async def screen_start(machine_id: str, body: ScreenActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await record_audit(db, event_type="screenshot_started", summary=f"Screen {body.mode} requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"mode": body.mode, "consent": body.consent})
    await db.commit()
    return command_response("screen_start", mode=body.mode, consent=body.consent)


@router.post("/machines/{machine_id}/screen/stop", response_model=MachineCommandOut)
async def screen_stop(machine_id: str, body: ScreenActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await record_audit(db, event_type="screenshot_stopped", summary="Screen view stopped", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"mode": body.mode})
    await db.commit()
    return command_response("screen_stop", mode=body.mode)


@router.post("/machines/{machine_id}/screen/capture", response_model=MachineCommandOut)
async def screen_capture(machine_id: str, body: ScreenActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await record_audit(db, event_type="screenshot_started", summary="Screenshot capture requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"mode": "capture", "consent": body.consent})
    await db.commit()
    return command_response("capture_screen", consent=body.consent)


@router.post("/machines/{machine_id}/webcam/start", response_model=MachineCommandOut)
async def webcam_start(machine_id: str, body: WebcamActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    if not body.consent:
        await record_audit(db, event_type="acl_denied", summary="Webcam start denied without consent", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webcam requires consent")
    await record_audit(db, event_type="webcam_started", summary="Webcam start requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"consent": body.consent})
    await db.commit()
    return command_response("webcam", start=True, consent=True)


@router.post("/machines/{machine_id}/webcam/stop", response_model=MachineCommandOut)
async def webcam_stop(machine_id: str, body: WebcamActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    await record_audit(db, event_type="webcam_stopped", summary="Webcam stop requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"consent": body.consent})
    await db.commit()
    return command_response("webcam", start=False, consent=body.consent)


@router.post("/machines/{machine_id}/webcam/snapshot", response_model=MachineCommandOut)
async def webcam_snapshot(machine_id: str, body: WebcamActionIn, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
    if not body.consent:
        await record_audit(db, event_type="webcam_denied", summary="Webcam snapshot denied without consent", actor_type="admin", actor_user_id=user.id, machine_id=machine_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="webcam requires consent")
    await record_audit(db, event_type="webcam_snapshot", summary="Webcam snapshot requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"consent": body.consent})
    await db.commit()
    return command_response("webcam_snapshot", consent=True)


@router.post("/machines/{machine_id}/power", response_model=MachineCommandOut)
async def power_action(
    machine_id: str,
    body: PowerActionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
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
    if action == "lock" and not reason:
        reason = "lock workstation"
    if action == "cancel" and not reason:
        reason = "cancel scheduled power action"
    event_type = f"{action}_requested" if action in {"restart", "shutdown"} else "power_cancel_requested" if action == "cancel" else "power_requested"
    await record_audit(db, event_type=event_type, summary=f"Power action requested: {action}", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"action": action, "reason": reason})
    await db.commit()
    return command_response("power", power_action=action, confirm=True, reason=reason)


@router.post("/machines/{machine_id}/file-dispatch", response_model=MachineCommandOut)
async def file_dispatch(
    machine_id: str,
    body: FileDispatchIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_UPLOAD)),
) -> MachineCommandOut:
    await require_machine_exists(db, machine_id)
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
    if body.path.startswith(("../", "..\\", "\\\\", "/", "C:", "c:")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="path traversal rejected")
    await record_audit(db, event_type="file_downloaded_from_agent", summary="Sandbox file download requested", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"path": body.path})
    await db.commit()
    return command_response("file_get", path=body.path)


@router.get("/machines/{machine_id}/sandbox/files", response_model=list[SandboxFileOut])
async def machine_sandbox_files(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> list[SandboxFileOut]:
    await require_machine_exists(db, machine_id)
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
    _: User = Depends(require_permission(Permission.JOBS_RUN)),
):
    await require_machine_exists(db, machine_id)
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
