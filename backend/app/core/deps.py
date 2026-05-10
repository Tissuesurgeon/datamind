"""FastAPI dependencies — auth, DB session, AI client, etc."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenPayload, decode_jwt
from app.db.session import session_scope
from app.models.user import User
from sqlalchemy import select


async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_token(authorization: str | None = Header(default=None)) -> TokenPayload:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_jwt(authorization.split(" ", 1)[1].strip())


async def get_current_user(
    db: DBSession,
    token: Annotated[TokenPayload, Depends(get_token)],
) -> User:
    res = await db.execute(select(User).where(User.id == token.sub))
    user = res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    db: DBSession,
    authorization: str | None = Header(default=None),
) -> User | None:
    """Public endpoints accept either an anonymous request or a logged-in one."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        token = decode_jwt(authorization.split(" ", 1)[1].strip())
    except HTTPException:
        return None
    res = await db.execute(select(User).where(User.id == token.sub))
    return res.scalar_one_or_none()


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
