from __future__ import annotations

import pytest

from apps.agent.app_manager import list_allowed_applications, start_application


def test_application_whitelist_is_exact_and_stable() -> None:
    assert [app["display_name"] for app in list_allowed_applications()] == ["Zalo", "Discord", "VSCode", "Chrome", "Notepad"]


@pytest.mark.parametrize(
    "value",
    [
        "cmd",
        "powershell",
        r"C:\Windows\System32\cmd.exe",
        " chrome ",
        "chrоme",  # Cyrillic o
        "chrome --incognito",
        "../chrome",
        "",
    ],
)
def test_application_key_fuzz_rejects_non_exact_whitelist_values(value: str) -> None:
    assert start_application(value)["error"] == "not_in_allowlist"
