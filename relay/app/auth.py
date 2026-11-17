"""Kiosk authentication. The relay stores only SHA-256 hashes of device tokens;
a lost Pi is revoked by deleting its entry."""

import hashlib
import hmac

from fastapi import Depends, Header, HTTPException

from .config import Settings, get_settings


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate_device(
    authorization: str = Header(default=""),
    x_device_id: str = Header(default=""),
    settings: Settings = Depends(get_settings),
) -> str:
    expected = settings.device_token_hashes.get(x_device_id)
    token = authorization.removeprefix("Bearer ")
    if not expected or not hmac.compare_digest(expected, hash_token(token)):
        raise HTTPException(401, "invalid device credentials")
    return x_device_id
