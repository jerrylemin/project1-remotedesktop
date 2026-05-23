from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.db import get_db
from apps.api.schemas import LoginIn, TokenOut
from apps.api.services.audit import record_audit
from apps.api.services.auth import authenticate

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenOut)
async def login(response: Response, body: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    authenticated = await authenticate(db, body.username, body.password)
    if authenticated is None:
        await record_audit(db, event_type="auth_failed", summary=f"Failed login for {body.username}", actor_type="system")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    user, token = authenticated
    await record_audit(db, event_type="admin_login", summary=f"{user.username} logged in", actor_type="admin", actor_user_id=user.id)
    await db.commit()
    response.set_cookie(get_settings().cookie_name, token, httponly=True, samesite="lax")
    return TokenOut(access_token=token)


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(get_settings().cookie_name)
    return {"status": "ok"}


@router.post("/admin/login")
async def login_form(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    token = await login(response, LoginIn(username=username, password=password), db)
    return {"status": "ok", "access_token": token.access_token}

