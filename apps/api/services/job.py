from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import Job
from shared.time_utils import utc_now


async def create_job(db: AsyncSession, machine_id: str, command: str, cwd: str | None, timeout: int) -> Job:
    job = Job(id=str(uuid4()), machine_id=machine_id, command=command, cwd=cwd, timeout=timeout, started_at=utc_now())
    db.add(job)
    await db.flush()
    return job


async def finish_job(db: AsyncSession, job: Job, stdout: str, stderr: str, exit_code: int) -> Job:
    job.stdout = stdout
    job.stderr = stderr
    job.exit_code = exit_code
    job.finished_at = utc_now()
    await db.flush()
    return job


async def get_job(db: AsyncSession, job_id: str) -> Job | None:
    return await db.scalar(select(Job).where(Job.id == job_id))


async def list_jobs_for_machine(db: AsyncSession, machine_id: str) -> list[Job]:
    result = await db.execute(select(Job).where(Job.machine_id == machine_id).order_by(Job.started_at.desc()))
    return list(result.scalars().all())
