from __future__ import annotations

from pathlib import Path

from apps.api.routers.auth import clear_login_attempts


async def test_login_rate_limit_blocks_repeated_failures(api_client) -> None:
    clear_login_attempts()
    for _ in range(5):
        response = await api_client.post("/auth/login", json={"username": "missing", "password": "wrong"})
        assert response.status_code == 401

    blocked = await api_client.post("/auth/login", json={"username": "missing", "password": "wrong"})

    assert blocked.status_code == 429


async def test_login_input_has_bounded_length(api_client) -> None:
    response = await api_client.post("/auth/login", json={"username": "u" * 129, "password": "p"})

    assert response.status_code == 422


def test_runtime_does_not_seed_or_print_default_admin_password() -> None:
    sources = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in ("main.py", "scripts/create_admin.py", "apps/api/seed.py")
    )

    assert 'default="admin123"' not in sources
    assert 'password: str = "admin123"' not in sources
    assert " / {args.password}" not in sources
