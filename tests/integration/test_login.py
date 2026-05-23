from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.services.auth import create_user


async def test_login_returns_token(api_client) -> None:
    async with SessionLocal() as db:
        await create_user(db, "admin", "admin123", role="admin")
        await db.commit()
    response = await api_client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert response.json()["access_token"]

