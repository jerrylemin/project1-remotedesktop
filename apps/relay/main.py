from __future__ import annotations

from fastapi import FastAPI

from apps.relay.router import router


def create_app() -> FastAPI:
    app = FastAPI(title="TelePC Relay", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
