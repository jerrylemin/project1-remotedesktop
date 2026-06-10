from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from apps.api.config import get_settings
from apps.api.models import User
from shared.crypto import random_secret
from shared.enums import ROLE_PERMISSIONS, Permission


@dataclass
class WsTicket:
    token: str
    user_id: int
    username: str
    permissions: set[str]
    expires_at: datetime
    used: bool = False


_tickets: dict[str, WsTicket] = {}


def _permissions_for(user: User) -> set[str]:
    role_names = {role.name for role in user.roles}
    permissions = set().union(*(ROLE_PERMISSIONS.get(name, set()) for name in role_names))
    return {permission.value for permission in permissions}


def create_ws_ticket(user: User) -> WsTicket:
    ttl = get_settings().ws_ticket_ttl_seconds
    ticket = WsTicket(
        token=random_secret(24),
        user_id=user.id,
        username=user.username,
        permissions=_permissions_for(user),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl),
    )
    _tickets[ticket.token] = ticket
    return ticket


def validate_ws_ticket(token: str, *, consume: bool = True) -> WsTicket | None:
    ticket = _tickets.get(token)
    if ticket is None or ticket.used or ticket.expires_at <= datetime.now(timezone.utc):
        return None
    if consume:
        ticket.used = True
    return ticket


def clear_ws_tickets() -> None:
    _tickets.clear()


def can_control(ticket: WsTicket) -> bool:
    return Permission.MACHINES_CONTROL.value in ticket.permissions

