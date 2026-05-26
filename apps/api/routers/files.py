from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import require_permission
from apps.api.models import User
from apps.api.schemas import SandboxFileOut
from apps.api.services.audit import record_audit
from apps.api.services.file import list_sandbox_files, record_dispatch, store_upload
from shared.enums import Permission

router = APIRouter(prefix="/api/files", tags=["files"])
artifact_router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_UPLOAD)),
) -> dict[str, object]:
    artifact = await store_upload(db, file, user.id)
    await record_audit(db, event_type="file_uploaded_to_server", summary=f"Uploaded {artifact.filename}", actor_type="admin", actor_user_id=user.id, metadata={"filename": artifact.filename, "sha256": artifact.sha256})
    await db.commit()
    return {"artifact_id": artifact.id, "filename": artifact.filename, "size": artifact.size, "sha256": artifact.sha256}


@artifact_router.post("/upload")
async def upload_artifact_alias(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_UPLOAD)),
) -> dict[str, object]:
    return await upload_file(file, db, user)


@router.post("/{artifact_id}/dispatch")
async def dispatch_file(
    artifact_id: str,
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.FILES_UPLOAD)),
) -> dict[str, str]:
    job_id = str(uuid4())
    sandbox_path = f"{machine_id}/{job_id}"
    await record_dispatch(db, artifact_id, machine_id, job_id, sandbox_path)
    await record_audit(db, event_type="file_dispatched_to_agent", summary="File dispatched to agent sandbox", actor_type="admin", actor_user_id=user.id, machine_id=machine_id, metadata={"artifact_id": artifact_id, "job_id": job_id})
    await db.commit()
    return {"job_id": job_id, "sandbox_path": sandbox_path}


@router.get("/machines/{machine_id}", response_model=list[SandboxFileOut])
async def machine_files(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.FILES_DOWNLOAD)),
) -> list[SandboxFileOut]:
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
