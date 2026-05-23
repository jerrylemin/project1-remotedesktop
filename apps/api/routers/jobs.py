from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import require_permission
from apps.api.models import User
from apps.api.schemas import JobCreateIn, JobOut
from apps.api.services.audit import record_audit
from apps.api.services.job import create_job, get_job
from shared.enums import Permission

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def job_out(job) -> JobOut:
    return JobOut(
        id=job.id,
        machine_id=job.machine_id,
        command=job.command,
        cwd=job.cwd,
        stdout=job.stdout,
        stderr=job.stderr,
        exit_code=job.exit_code,
        timeout=job.timeout,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.post("", response_model=JobOut)
async def jobs_create(
    body: JobCreateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.JOBS_RUN)),
) -> JobOut:
    job = await create_job(db, body.machine_id, body.command, body.cwd, body.timeout)
    await record_audit(db, event_type="sandbox_job_started", summary="Sandbox job requested", actor_type="admin", actor_user_id=user.id, machine_id=body.machine_id, metadata={"command": body.command, "job_id": job.id})
    await db.commit()
    return job_out(job)


@router.get("/{job_id}", response_model=JobOut)
async def jobs_get(job_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_permission(Permission.JOBS_RUN))) -> JobOut:
    job = await get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job_out(job)

