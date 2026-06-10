from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from apps.api.config import get_settings
from shared.crypto import hash_secret, verify_secret

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return hash_secret(password)


def verify_password(password: str, password_hash: str) -> bool:
    return verify_secret(password, password_hash)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires}
    payload.update(extra or {})
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])

