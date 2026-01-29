"""
Authentication endpoints: register, login, logout, and token refresh.
"""

from fastapi import APIRouter, Cookie, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import MessageResponse
from app.schemas.user import UserCreate, UserResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user.

    Args:
        user_in: User registration data (email and password).
        db: Database session.

    Returns:
        The newly created user.

    Raises:
        EmailAlreadyExistsException: If email is already registered.
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalars().first()

    if existing_user:
        logger.warning(f"Registration attempt with existing email: {user_in.email}")
        raise EmailAlreadyExistsException()

    # Create user with hashed password
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"New user registered: {user_in.email}")
    return new_user


@router.post("/login", response_model=MessageResponse)
async def login(
    response: Response,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> MessageResponse:
    """
    Authenticate user and set JWT tokens in HttpOnly cookies.

    Args:
        response: FastAPI response object for setting cookies.
        db: Database session.
        form_data: OAuth2 form with username (email) and password.

    Returns:
        Success message.

    Raises:
        InvalidCredentialsException: If credentials are invalid.
        InactiveUserException: If user account is inactive.
    """
    # Authenticate user
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise InvalidCredentialsException()

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {form_data.username}")
        raise InactiveUserException()

    # Create tokens
    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)

    # Set HttpOnly cookies
    # httponly=True: JavaScript cannot read it (XSS protection)
    # samesite="lax": Basic CSRF protection
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )

    logger.info(f"User logged in: {user.email}")
    return MessageResponse(message="Login successful")


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
