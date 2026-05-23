from __future__ import annotations

from fastapi import Header, HTTPException, status

from apps.api.config import get_settings


async def require_internal_secret(x_telepc_internal_secret: str | None = Header(default=None)) -> None:
    if x_telepc_internal_secret != get_settings().internal_api_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid internal secret")

