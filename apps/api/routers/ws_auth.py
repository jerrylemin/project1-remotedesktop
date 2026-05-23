from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from apps.api.deps import get_current_user
from apps.api.deps_internal import require_internal_secret
from apps.api.models import User
from apps.api.services.ws_ticket import can_control, create_ws_ticket, validate_ws_ticket

router = APIRouter(tags=["ws-auth"])


class WsTicketOut(BaseModel):
    ws_ticket: str
    expires_at: str


class WsTicketValidateIn(BaseModel):
    ws_ticket: str


class WsTicketValidateOut(BaseModel):
    user_id: int
    username: str
    permissions: list[str]
    can_control: bool


@router.post("/api/ws-ticket", response_model=WsTicketOut)
async def issue_ws_ticket(user: User = Depends(get_current_user)) -> WsTicketOut:
    ticket = create_ws_ticket(user)
    return WsTicketOut(ws_ticket=ticket.token, expires_at=ticket.expires_at.isoformat())


@router.post("/internal/ws-ticket/validate", response_model=WsTicketValidateOut, dependencies=[Depends(require_internal_secret)])
async def validate_ws_ticket_internal(body: WsTicketValidateIn) -> WsTicketValidateOut:
    ticket = validate_ws_ticket(body.ws_ticket)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired ws ticket")
    return WsTicketValidateOut(
        user_id=ticket.user_id,
        username=ticket.username,
        permissions=sorted(ticket.permissions),
        can_control=can_control(ticket),
    )

