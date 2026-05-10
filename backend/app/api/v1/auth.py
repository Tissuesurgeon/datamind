"""Auth API: SIWE-style nonce + verify, plus Privy token verification."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import CurrentUser, DBSession
from app.core.security import issue_jwt
from app.schemas.auth import (
    NonceRequest,
    NonceResponse,
    PrivyVerifyRequest,
    SiweVerifyRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth import (
    PrivyVerificationError,
    create_or_get_user,
    get_nonce_store,
    verify_privy_token,
    verify_siwe_signature,
)
from app.services.auth.privy import NonceStore

router = APIRouter()


@router.post("/nonce", response_model=NonceResponse)
async def request_nonce(req: NonceRequest) -> NonceResponse:
    store = get_nonce_store()
    entry = store.issue(req.wallet_address)
    return NonceResponse(
        nonce=entry.nonce,
        message=NonceStore.message(req.wallet_address, entry.nonce),
        expires_at=datetime.fromtimestamp(entry.expires_at, tz=timezone.utc),
    )


@router.post("/siwe/verify", response_model=TokenResponse)
async def verify_siwe(req: SiweVerifyRequest, db: DBSession) -> TokenResponse:
    """Verify SIWE-style signature → issue session JWT.

    In demo / mock mode (no Privy), this is the primary auth path.
    """
    store = get_nonce_store()
    if not store.consume(req.wallet_address, req.nonce):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid nonce")

    msg = NonceStore.message(req.wallet_address, req.nonce)
    if not verify_siwe_signature(
        wallet=req.wallet_address, message=msg, signature=req.signature
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad signature")

    user = await create_or_get_user(
        db,
        wallet_address=req.wallet_address,
        display_name=req.display_name,
        email=req.email,
    )
    token = issue_jwt(user_id=user.id, wallet=user.wallet_address)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/privy/verify", response_model=TokenResponse)
async def verify_privy(req: PrivyVerifyRequest, db: DBSession) -> TokenResponse:
    """Verify a Privy identity token (live) → issue session JWT.

    If Privy isn't configured, treat the supplied wallet_address as ground truth
    (demo mode) — the frontend's mock wallet drops a fake token and a wallet hint.
    """
    settings = get_settings()
    wallet = (req.wallet_address or "").strip()

    if settings.privy_live:
        try:
            payload = await verify_privy_token(req.privy_token)
        except PrivyVerificationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"privy verification failed: {exc}",
            ) from exc
        # Privy puts the linked accounts under "linked_accounts"
        linked = payload.get("linked_accounts") or []
        for acc in linked:
            if acc.get("type", "").startswith("wallet"):
                wallet = acc.get("address", wallet)
                break
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="no wallet linked to Privy account",
            )
    else:
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="wallet_address required in mock mode",
            )

    user = await create_or_get_user(
        db,
        wallet_address=wallet,
        display_name=req.display_name,
        email=req.email,
    )
    token = issue_jwt(user_id=user.id, wallet=user.wallet_address)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/health")
async def auth_health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "privy_live": settings.privy_live,
        "ts": int(time.time()),
    }
