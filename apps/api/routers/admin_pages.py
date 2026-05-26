from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.db import get_db
from apps.api.deps import cookie_name
from apps.api.models import User
from apps.api.security import decode_access_token
from shared.enums import ROLE_PERMISSIONS, Permission

templates = Jinja2Templates(directory="apps/api/templates")
router = APIRouter(tags=["admin-pages"])


async def require_admin_session(
    request: Request,
    permission: Permission,
    db: AsyncSession,
) -> User | RedirectResponse | HTMLResponse:
    token = request.cookies.get(cookie_name())
    if not token:
        return RedirectResponse("/admin/login", status_code=302)
    try:
        payload = decode_access_token(token)
    except Exception:
        return RedirectResponse("/admin/login", status_code=302)
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.username == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return RedirectResponse("/admin/login", status_code=302)
    role_names = {role.name for role in user.roles}
    permissions = set().union(*(ROLE_PERMISSIONS.get(name, set()) for name in role_names))
    if permission not in permissions:
        return templates.TemplateResponse(request, "403.html", {"user": user}, status_code=403)
    return user


def page_permission(permission: Permission):
    async def dependency(request: Request, db: AsyncSession = Depends(get_db)) -> User | RedirectResponse | HTMLResponse:
        return await require_admin_session(request, permission, db)

    return dependency


def denied_or_user(value: User | RedirectResponse | HTMLResponse) -> RedirectResponse | HTMLResponse | None:
    if isinstance(value, (RedirectResponse, HTMLResponse)):
        return value
    return None


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse("/admin/dashboard")


@router.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html")


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, guard: User | RedirectResponse | HTMLResponse = Depends(page_permission(Permission.MACHINES_READ))) -> HTMLResponse:
    if response := denied_or_user(guard):
        return response
    return templates.TemplateResponse(request, "dashboard.html")


@router.get("/admin/machines", response_class=HTMLResponse)
async def machines_page(request: Request, guard: User | RedirectResponse | HTMLResponse = Depends(page_permission(Permission.MACHINES_READ))) -> HTMLResponse:
    if response := denied_or_user(guard):
        return response
    return templates.TemplateResponse(request, "machines.html")


@router.get("/admin/machines/{machine_id}", response_class=HTMLResponse)
async def machine_page(
    request: Request,
    machine_id: str,
    guard: User | RedirectResponse | HTMLResponse = Depends(page_permission(Permission.MACHINES_CONTROL)),
) -> HTMLResponse:
    if response := denied_or_user(guard):
        return response
    return templates.TemplateResponse(request, "machine_detail.html", {"machine_id": machine_id})


@router.get("/admin/audit", response_class=HTMLResponse)
async def audit_page(request: Request, guard: User | RedirectResponse | HTMLResponse = Depends(page_permission(Permission.AUDIT_READ))) -> HTMLResponse:
    if response := denied_or_user(guard):
        return response
    return templates.TemplateResponse(request, "audit.html")


@router.get("/admin/files", response_class=HTMLResponse)
async def files_page(request: Request, guard: User | RedirectResponse | HTMLResponse = Depends(page_permission(Permission.FILES_DOWNLOAD))) -> HTMLResponse:
    if response := denied_or_user(guard):
        return response
    return templates.TemplateResponse(request, "machines.html")


@router.get("/admin/settings", response_class=HTMLResponse)
async def settings_page(request: Request, guard: User | RedirectResponse | HTMLResponse = Depends(page_permission(Permission.ADMIN_MANAGE))) -> HTMLResponse:
    if response := denied_or_user(guard):
        return response
    return templates.TemplateResponse(request, "dashboard.html")
