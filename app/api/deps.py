"""
API dependencies for authentication and database access.
"""

from typing import Annotated

from fastapi import Cookie, Depends
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import CredentialsException, InactiveUserException
from app.db.session import get_db
from app.models.user import User


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: str | None = Cookie(default=None),
) -> User:
    """
    Validate access token from HttpOnly cookie and return the current user.

    Args:
        db: Database session from dependency injection.
        access_token: JWT access token from HttpOnly cookie.

    Returns:
        The authenticated User object.

    Raises:
        CredentialsException: If token is missing, invalid, or user not found.
        InactiveUserException: If user account is inactive.
    """
    # Check if cookie exists
    if not access_token:
        raise CredentialsException()

    # Clean token (remove "Bearer " prefix if present)
    token_str = access_token.removeprefix("Bearer ")

    try:
        # Decode and verify signature
        payload = jwt.decode(
            token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")

        if email is None:
            raise CredentialsException()

    except JWTError:
        raise CredentialsException()

    # Retrieve user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None:
        raise CredentialsException()

    if not user.is_active:
        raise InactiveUserException()

    return user
