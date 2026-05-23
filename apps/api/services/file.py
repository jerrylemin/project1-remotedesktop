from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.models import Artifact, SandboxFile


async def store_upload(db: AsyncSession, upload: UploadFile, uploaded_by: int | None) -> Artifact:
    settings = get_settings()
    original = Path(upload.filename or "upload.bin")
    ext = original.suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file extension not allowed")
    data = await upload.read()
    if len(data) > settings.max_upload_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large")
    artifact_id = str(uuid4())
    filename = f"{artifact_id}{ext}"
    storage_path = settings.artifact_root / filename
    storage_path.write_bytes(data)
    artifact = Artifact(
        id=artifact_id,
        filename=filename,
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        mime=mimetypes.guess_type(filename)[0] or "application/octet-stream",
        stored_path=str(storage_path),
        uploaded_by=uploaded_by,
    )
    db.add(artifact)
    await db.flush()
    return artifact


async def record_dispatch(db: AsyncSession, artifact_id: str, machine_id: str, job_id: str, sandbox_path: str) -> SandboxFile:
    item = SandboxFile(artifact_id=artifact_id, machine_id=machine_id, job_id=job_id, sandbox_path=sandbox_path)
    db.add(item)
    await db.flush()
    return item


async def list_sandbox_files(db: AsyncSession, machine_id: str) -> list[tuple[SandboxFile, Artifact]]:
    result = await db.execute(
        select(SandboxFile, Artifact)
        .join(Artifact, SandboxFile.artifact_id == Artifact.id)
        .where(SandboxFile.machine_id == machine_id)
        .order_by(Artifact.created_at.desc())
    )
    return list(result.all())
