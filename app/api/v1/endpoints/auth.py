"""
Authentication endpoints: token refresh and logout.

Note: Registration and login are handled via passkeys.
See passkey.py for WebAuthn-based authentication.
"""

from fastapi import APIRouter, Cookie, Response
from jose import jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenException
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.schemas.token import MessageResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post("/refresh", response_model=MessageResponse)
async def refresh_token_endpoint(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
) -> MessageResponse:
    """
    Use refresh token to generate a new access token.

    Args:
        response: FastAPI response object for setting cookies.
        refresh_token: Refresh token from HttpOnly cookie.

    Returns:
        Success message.

    Raises:
        InvalidTokenException: If refresh token is missing or invalid.
    """
    if not refresh_token:
        raise InvalidTokenException("Refresh token missing")

    try:
        # Decode and validate token
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "refresh":
            raise InvalidTokenException()

        # Create new access token
        new_access_token = create_access_token(email)

        # Update access token cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
        )

        logger.debug(f"Token refreshed for: {email}")
        return MessageResponse(message="Token refreshed")

    except jwt.JWTError:
        logger.warning("Invalid refresh token attempt")
        raise InvalidTokenException("Invalid refresh token")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    """
    Clear authentication cookies to log out user.

    Args:
        response: FastAPI response object for deleting cookies.

    Returns:
        Success message.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logout successful")
