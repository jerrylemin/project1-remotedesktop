from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apps.api.db import init_db
from apps.api.routers import admin_pages, audit, auth, dashboard, files, internal, jobs, machines, sessions, ws_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="TelePC API", version="0.1.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory="apps/api/static"), name="static")
    app.include_router(auth.router)
    app.include_router(admin_pages.router)
    app.include_router(dashboard.router)
    app.include_router(machines.router)
    app.include_router(sessions.router)
    app.include_router(audit.router)
    app.include_router(files.router)
    app.include_router(jobs.router)
    app.include_router(ws_auth.router)
    app.include_router(internal.router)

    return app


app = create_app()
