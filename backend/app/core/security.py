"""JWT issuance + verification."""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings


@dataclass(frozen=True)
class TokenPayload:
    sub: str           # user id (uuid)
    wallet: str        # wallet address (lowercased)
    exp: int


def issue_jwt(*, user_id: str, wallet: str) -> str:
    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": user_id,
        "wallet": wallet.lower(),
        "iat": now,
        "exp": now + settings.jwt_ttl_seconds,
        "iss": "datamind",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_alg,
    )


def decode_jwt(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        decoded = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_alg],
            options={"require": ["sub", "wallet", "exp"]},
            issuer="datamind",
        )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token expired",
        ) from e
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {e}",
        ) from e
    return TokenPayload(sub=decoded["sub"], wallet=decoded["wallet"], exp=decoded["exp"])
