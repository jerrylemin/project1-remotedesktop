from __future__ import annotations

import pytest
import pytest_asyncio
import os
import sys
import tempfile
from pathlib import Path
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"telepc_pytest_{os.getpid()}.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}")

for stale_path in (TEST_DB_PATH, TEST_DB_PATH.with_name(f"{TEST_DB_PATH.name}-journal")):
    try:
        stale_path.unlink()
    except FileNotFoundError:
        pass

from apps.api.db import Base, SessionLocal, engine
from apps.api.main import app
from apps.api.services.auth import create_user


def pytest_sessionfinish(session, exitstatus):
    for stale_path in (TEST_DB_PATH, TEST_DB_PATH.with_name(f"{TEST_DB_PATH.name}-journal")):
        try:
            stale_path.unlink()
        except FileNotFoundError:
            pass


@pytest_asyncio.fixture
async def clean_db():
    from apps.api import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def admin_token(clean_db) -> str:
    async with SessionLocal() as db:
        await create_user(db, "admin", "admin123", role="admin")
        await db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def api_client(clean_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
