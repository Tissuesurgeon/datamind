"""Auth-related request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class NonceRequest(BaseModel):
    wallet_address: str = Field(min_length=4, max_length=64)


class NonceResponse(BaseModel):
    nonce: str
    message: str
    expires_at: datetime


class SiweVerifyRequest(BaseModel):
    """Plain SIWE-style verification used in mock mode."""

    wallet_address: str
    nonce: str
    signature: str
    display_name: str | None = None
    email: EmailStr | None = None


class PrivyVerifyRequest(BaseModel):
    """Privy-issued JWT verification.

    The frontend sends Privy's identity token; the backend validates it,
    extracts the wallet address, and issues a DataMind session JWT.
    """

    privy_token: str
    wallet_address: str | None = None  # optional hint
    display_name: str | None = None
    email: EmailStr | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    wallet_address: str
    display_name: str | None
    email: EmailStr | None
    avatar_url: str | None
    created_at: datetime


TokenResponse.model_rebuild()
