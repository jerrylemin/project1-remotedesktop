from __future__ import annotations

from time import monotonic

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.db import get_db
from apps.api.schemas import LoginIn, TokenOut
from apps.api.services.audit import record_audit
from apps.api.services.auth import authenticate

router = APIRouter(tags=["auth"])
_login_failures: dict[str, list[float]] = {}
LOGIN_WINDOW_SECONDS = 60
LOGIN_FAILURE_LIMIT = 5


def clear_login_attempts() -> None:
    _login_failures.clear()


def _login_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{username.casefold()}"


def _check_login_limit(key: str) -> None:
    cutoff = monotonic() - LOGIN_WINDOW_SECONDS
    attempts = [value for value in _login_failures.get(key, []) if value > cutoff]
    _login_failures[key] = attempts
    if len(attempts) >= LOGIN_FAILURE_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many login attempts")


@router.post("/auth/login", response_model=TokenOut)
async def login(request: Request, response: Response, body: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    key = _login_key(request, body.username)
    _check_login_limit(key)
    authenticated = await authenticate(db, body.username, body.password)
    if authenticated is None:
        _login_failures.setdefault(key, []).append(monotonic())
        await record_audit(db, event_type="auth_failed", summary=f"Failed login for {body.username}", actor_type="system")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    user, token = authenticated
    _login_failures.pop(key, None)
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
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    token = await login(request, response, LoginIn(username=username, password=password), db)
    return {"status": "ok", "access_token": token.access_token}

