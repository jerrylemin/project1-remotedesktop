from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="apps/api/templates")
router = APIRouter(tags=["admin-pages"])


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse("/admin/dashboard")


@router.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/admin/machines", response_class=HTMLResponse)
async def machines_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("machines.html", {"request": request})


@router.get("/admin/machines/{machine_id}", response_class=HTMLResponse)
async def machine_page(request: Request, machine_id: str) -> HTMLResponse:
    return templates.TemplateResponse("machine_detail.html", {"request": request, "machine_id": machine_id})


@router.get("/admin/audit", response_class=HTMLResponse)
async def audit_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("audit.html", {"request": request})

