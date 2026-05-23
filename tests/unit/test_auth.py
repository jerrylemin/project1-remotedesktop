from __future__ import annotations

from apps.api.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify() -> None:
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)


def test_token_encode_decode() -> None:
    token = create_access_token("admin", {"uid": 1})
    payload = decode_access_token(token)
    assert payload["sub"] == "admin"
    assert payload["uid"] == 1

