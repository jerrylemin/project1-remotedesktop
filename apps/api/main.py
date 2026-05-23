from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from apps.api.db import init_db
from apps.api.routers import admin_pages, audit, auth, files, jobs, machines, sessions


def create_app() -> FastAPI:
    app = FastAPI(title="TelePC API", version="0.1.0")
    app.mount("/static", StaticFiles(directory="apps/api/static"), name="static")
    app.include_router(auth.router)
    app.include_router(admin_pages.router)
    app.include_router(machines.router)
    app.include_router(sessions.router)
    app.include_router(audit.router)
    app.include_router(files.router)
    app.include_router(jobs.router)

    @app.on_event("startup")
    async def on_startup() -> None:
        await init_db()

    return app


app = create_app()
