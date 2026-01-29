"""
Security utilities for password hashing and JWT token management.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Configure password hashing algorithm (Argon2id - recommended)
password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a secure hash of a password using Argon2id.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.
    """
    return password_hash.hash(password)


def create_access_token(subject: str | Any) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject to encode in the token (typically user email).

    Returns:
        The encoded JWT access token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: The subject to encode in the token (typically user email).

    Returns:
        The encoded JWT refresh token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
