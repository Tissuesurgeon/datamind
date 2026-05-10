"""Wallet auth — Privy-token verification (live) + SIWE (mock fallback).

In mock mode (no `PRIVY_APP_ID`), we accept a SIWE-style nonce/signature pair.
The signature is recovered with `eth_account` and the wallet must match.

In live mode, we verify the Privy identity token via JWKS.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import jwt
from eth_account.messages import encode_defunct
from eth_account import Account
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import User
from app.utils.ids import short_token

log = get_logger(__name__)

PRIVY_JWKS_URL = "https://auth.privy.io/api/v1/apps/{app_id}/jwks.json"


class PrivyVerificationError(Exception):
    pass


# ----------------------------------------------------------------------------- #
# In-process nonce store. Backed by Redis in real deployment via WSManager Redis,
# but this is fine for a hackathon-scale single-node demo.
# ----------------------------------------------------------------------------- #


@dataclass
class _NonceEntry:
    wallet: str
    nonce: str
    expires_at: float


class NonceStore:
    """Tiny in-process store for SIWE nonces. TTL: 10 minutes."""

    TTL_SECONDS = 600

    def __init__(self) -> None:
        self._store: dict[str, _NonceEntry] = {}

    def issue(self, wallet: str) -> _NonceEntry:
        wallet = wallet.lower()
        nonce = short_token(16)
        entry = _NonceEntry(
            wallet=wallet, nonce=nonce, expires_at=time.time() + self.TTL_SECONDS
        )
        self._store[wallet] = entry
        return entry

    def consume(self, wallet: str, nonce: str) -> bool:
        wallet = wallet.lower()
        entry = self._store.get(wallet)
        if entry is None:
            return False
        if entry.expires_at < time.time():
            self._store.pop(wallet, None)
            return False
        if entry.nonce != nonce:
            return False
        self._store.pop(wallet, None)
        return True

    @staticmethod
    def message(wallet: str, nonce: str) -> str:
        return (
            "DataMind wants you to sign in with your wallet:\n"
            f"{wallet.lower()}\n\n"
            "Decentralized AI Data Economy.\n\n"
            f"Nonce: {nonce}\n"
            "Expires in 10 minutes."
        )


_singleton: NonceStore | None = None


def get_nonce_store() -> NonceStore:
    global _singleton
    if _singleton is None:
        _singleton = NonceStore()
    return _singleton


# ----------------------------------------------------------------------------- #
# Verification primitives                                                       #
# ----------------------------------------------------------------------------- #


def verify_siwe_signature(*, wallet: str, message: str, signature: str) -> bool:
    """Recover the signer from `message`/`signature` and compare to `wallet`."""
    try:
        encoded = encode_defunct(text=message)
        recovered = Account.recover_message(encoded, signature=signature)
    except Exception as exc:
        log.warning("siwe.recover.failed", error=str(exc))
        return False
    return recovered.lower() == wallet.lower()


async def verify_privy_token(token: str) -> dict:
    """Verify a Privy identity token (live mode only).

    Returns the decoded payload. Raises `PrivyVerificationError` on failure.
    """
    settings = get_settings()
    if not settings.privy_live:
        raise PrivyVerificationError("privy not configured")

    jwks_url = PRIVY_JWKS_URL.format(app_id=settings.privy_app_id)
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise PrivyVerificationError(f"jwks fetch failed: {exc}") from exc
        jwks = resp.json()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise PrivyVerificationError(f"bad header: {exc}") from exc

    kid = unverified_header.get("kid")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise PrivyVerificationError("kid not found in JWKS")

    public_key = jwt.algorithms.ECAlgorithm.from_jwk(key)
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[unverified_header.get("alg", "ES256")],
            audience=settings.privy_app_id,
        )
    except jwt.PyJWTError as exc:
        raise PrivyVerificationError(f"verification failed: {exc}") from exc

    return payload


# ----------------------------------------------------------------------------- #
# Persistence                                                                    #
# ----------------------------------------------------------------------------- #


async def create_or_get_user(
    db: AsyncSession,
    *,
    wallet_address: str,
    display_name: str | None = None,
    email: str | None = None,
) -> User:
    wallet = wallet_address.lower().strip()
    res = await db.execute(select(User).where(User.wallet_address == wallet))
    user = res.scalar_one_or_none()
    if user is not None:
        if display_name and not user.display_name:
            user.display_name = display_name
        if email and not user.email:
            user.email = email
        await db.flush()
        return user
    user = User(
        wallet_address=wallet,
        display_name=display_name,
        email=email,
    )
    db.add(user)
    await db.flush()
    return user
