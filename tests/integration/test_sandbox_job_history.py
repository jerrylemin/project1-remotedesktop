from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.services.job import create_job, finish_job


async def test_sandbox_job_history(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        job = await create_job(db, "m1", "python demo.py", None, 5)
        await finish_job(db, job, "hello output", "", 0)
        await db.commit()
    response = await api_client.get("/api/jobs/machines/m1/history", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["status"] == "finished"
    assert rows[0]["stdout_preview"] == "hello output"
