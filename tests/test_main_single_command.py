from __future__ import annotations

import main
from apps.api.seed import admin_user_exists, seed_admin


def test_first_main_run_prompts_and_creates_admin(monkeypatch) -> None:
    created: list[tuple[str, str, bool]] = []
    passwords = iter(["StrongPass123!", "StrongPass123!"])

    async def no_admin() -> bool:
        return False

    async def fake_seed(username: str, password: str, *, include_demo_machines: bool = False) -> None:
        created.append((username, password, include_demo_machines))

    monkeypatch.setattr(main, "admin_user_exists", no_admin)
    monkeypatch.setattr(main, "seed_admin", fake_seed)
    monkeypatch.setattr(main.getpass, "getpass", lambda _prompt: next(passwords))

    main.ensure_admin_ready("admin", None, include_demo_machines=False)

    assert created == [("admin", "StrongPass123!", False)]


def test_later_main_runs_reuse_existing_admin_without_prompt(monkeypatch) -> None:
    async def admin_exists() -> bool:
        return True

    async def unexpected_seed(*args, **kwargs) -> None:
        raise AssertionError("existing admin must not be recreated")

    monkeypatch.setattr(main, "admin_user_exists", admin_exists)
    monkeypatch.setattr(main, "seed_admin", unexpected_seed)
    monkeypatch.setattr(
        main.getpass,
        "getpass",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("must not prompt")),
    )

    main.ensure_admin_ready("admin", None)


async def test_admin_detection_uses_the_initialized_database(clean_db) -> None:
    assert await admin_user_exists() is False

    await seed_admin("admin", "StrongPass123!")

    assert await admin_user_exists() is True
