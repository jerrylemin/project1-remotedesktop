from __future__ import annotations

import hashlib
import hmac
import secrets


def random_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_secret(secret: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_secret(secret: str, hashed: str) -> bool:
    try:
        algorithm, salt, expected = hashed.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    actual = hash_secret(secret, salt).split("$", 2)[2]
    return hmac.compare_digest(actual, expected)

