from __future__ import annotations

from shared.enums import ROLE_PERMISSIONS, Permission


def test_permission_matrix() -> None:
    assert Permission.ADMIN_MANAGE in ROLE_PERMISSIONS["admin"]
    assert Permission.MACHINES_CONTROL in ROLE_PERMISSIONS["teacher"]
    assert Permission.AUDIT_READ in ROLE_PERMISSIONS["auditor"]
    assert Permission.MACHINES_CONTROL not in ROLE_PERMISSIONS["auditor"]

