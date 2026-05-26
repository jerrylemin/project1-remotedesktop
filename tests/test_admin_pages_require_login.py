from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.services.auth import create_user


async def test_anonymous_admin_dashboard_redirects(api_client) -> None:
    response = await api_client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/login"


async def test_logged_in_admin_dashboard_renders(api_client) -> None:
    async with SessionLocal() as db:
        await create_user(db, "admin", "admin123", role="admin")
        await db.commit()
    login = await api_client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    api_client.cookies.set("telepc_session", login.json()["access_token"])
    response = await api_client.get("/admin/dashboard")
    assert response.status_code == 200


async def test_auditor_cannot_open_machine_control_page(api_client) -> None:
    async with SessionLocal() as db:
        await create_user(db, "audit", "audit123", role="auditor")
        await db.commit()
    login = await api_client.post("/auth/login", json={"username": "audit", "password": "audit123"})
    api_client.cookies.set("telepc_session", login.json()["access_token"])
    response = await api_client.get("/admin/machines/m1")
    assert response.status_code == 403
