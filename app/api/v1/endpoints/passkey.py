"""
Passkey (WebAuthn) endpoints for passwordless authentication.

Provides endpoints for:
- Registration: Create new user with passkey
- Authentication: Login with existing passkey
- Management: List, rename, delete passkeys
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from webauthn.helpers import base64url_to_bytes

from app.api.deps import get_current_active_user
from app.core.cache import get_challenge as redis_get_challenge
from app.core.cache import store_challenge as redis_store_challenge
from app.core.config import settings
from app.core.exceptions import (
    ChallengeNotFoundException,
    InactiveUserException,
    PasskeyAuthenticationFailedException,
    PasskeyNotFoundException,
    PasskeyRegistrationFailedException,
    UserNotFoundException,
)
from app.core.logging import get_logger
from app.core.security import create_access_token, create_refresh_token
from app.core.webauthn import (
    get_authentication_options,
    get_registration_options,
    verify_authentication,
    verify_registration,
)
from app.db.session import get_db
from app.models.passkey import Passkey
from app.models.user import User
from app.schemas.passkey import (
    PasskeyListResponse,
    PasskeyLoginBeginRequest,
    PasskeyLoginBeginResponse,
    PasskeyLoginCompleteRequest,
    PasskeyRegisterBeginRequest,
    PasskeyRegisterBeginResponse,
    PasskeyRegisterCompleteRequest,
    PasskeyResponse,
    PasskeyUpdateRequest,
)
from app.schemas.token import MessageResponse
from app.schemas.user import UserResponse

logger = get_logger(__name__)
router = APIRouter()


async def _store_challenge(
    email: str, challenge: bytes, display_name: str | None = None
) -> None:
    """Store challenge in Redis for later verification."""
    # Store as: 4-byte length prefix + challenge_bytes + metadata_json
    # This avoids issues if challenge contains separator characters
    metadata = json.dumps({"display_name": display_name}).encode()
    challenge_len = len(challenge).to_bytes(4, "big")
    value = challenge_len + challenge + metadata
    await redis_store_challenge(email, value)


async def _get_and_clear_challenge(email: str) -> tuple[bytes, str | None]:
    """Get and remove stored challenge from Redis. Raises if not found."""
    value = await redis_get_challenge(email)
    if not value:
        raise ChallengeNotFoundException()

    # Parse: 4-byte length prefix + challenge_bytes + metadata_json
    challenge_len = int.from_bytes(value[:4], "big")
    challenge = value[4 : 4 + challenge_len]
    display_name = None

    metadata_bytes = value[4 + challenge_len :]
    if metadata_bytes:
        try:
            metadata = json.loads(metadata_bytes)
            display_name = metadata.get("display_name")
        except json.JSONDecodeError:
            pass

    return challenge, display_name


# =============================================================================
# Registration Endpoints
# =============================================================================


@router.post("/register/begin", response_model=PasskeyRegisterBeginResponse)
async def register_begin(
    request: PasskeyRegisterBeginRequest,
    db: AsyncSession = Depends(get_db),
) -> PasskeyRegisterBeginResponse:
    """
    Start passkey registration for a new or existing user.

    Step 1 of 2 in the registration flow.

    Args:
        request: Contains email and optional display name.
        db: Database session.

    Returns:
        WebAuthn options for navigator.credentials.create()
    """
    # Check if user already exists
    result = await db.execute(
        select(User)
        .where(User.email == request.email)
        .options(selectinload(User.passkeys))
    )
    existing_user = result.scalars().first()

    if existing_user:
        # User exists - this will add another passkey
        user_id = str(existing_user.id).encode()
        existing_credentials = existing_user.passkeys
        display_name = existing_user.display_name or request.display_name
        logger.info(f"Adding new passkey for existing user: {request.email}")
    else:
        # New user - use email hash as temporary ID
        user_id = request.email.encode()
        existing_credentials = []
        display_name = request.display_name
        logger.info(f"Starting registration for new user: {request.email}")

    # Generate WebAuthn options
    options, challenge = get_registration_options(
        user_id=user_id,
        user_email=request.email,
        user_display_name=display_name,
        existing_credentials=existing_credentials,
    )

    # Store challenge for verification
    await _store_challenge(request.email, challenge, request.display_name)

    return PasskeyRegisterBeginResponse(options=options)


@router.post("/register/complete", response_model=UserResponse)
async def register_complete(
    request: PasskeyRegisterCompleteRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Complete passkey registration.

    Step 2 of 2 in the registration flow.
    Creates user if new, adds passkey, and returns JWT tokens in cookies.

    Args:
        request: Contains email and credential from browser.
        response: FastAPI response for setting cookies.
        db: Database session.

    Returns:
        The user data.
    """
    # Get stored challenge
    challenge, display_name = await _get_and_clear_challenge(request.email)

    # Verify the registration response
    try:
        verified = verify_registration(
            credential=request.credential,
            expected_challenge=challenge,
        )
    except Exception as e:
        logger.warning(f"Passkey registration verification failed: {e}")
        raise PasskeyRegistrationFailedException(str(e))

    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()

    if not user:
        # Create new user
        user = User(
            email=request.email,
            display_name=display_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()  # Get the user ID
        logger.info(f"Created new user: {request.email}")

    # Determine transports from credential (if available)
    transports = None
    if (
        "response" in request.credential
        and "transports" in request.credential["response"]
    ):
        transports = json.dumps(request.credential["response"]["transports"])

    # Create passkey
    passkey = Passkey(
        user_id=user.id,
        credential_id=verified["credential_id"],
        public_key=verified["public_key"],
        sign_count=verified["sign_count"],
        device_type=verified["device_type"],
        backed_up=verified["backed_up"],
        transports=transports,
        name=request.passkey_name,
    )
    db.add(passkey)
    await db.commit()
    await db.refresh(user)

    logger.info(f"Registered passkey for user: {request.email}")

    # Set JWT tokens in cookies
    _set_auth_cookies(response, user.email)

    return user


# =============================================================================
# Authentication Endpoints
# =============================================================================


@router.post("/login/begin", response_model=PasskeyLoginBeginResponse)
async def login_begin(
    request: PasskeyLoginBeginRequest,
    db: AsyncSession = Depends(get_db),
) -> PasskeyLoginBeginResponse:
    """
    Start passkey authentication.

    Step 1 of 2 in the login flow.

    Args:
        request: Contains email.
        db: Database session.

    Returns:
        WebAuthn options for navigator.credentials.get()
    """
    # Find user with passkeys
    result = await db.execute(
        select(User)
        .where(User.email == request.email)
        .options(selectinload(User.passkeys))
    )
    user = result.scalars().first()

    if not user:
        logger.warning(f"Login attempt for non-existent user: {request.email}")
        raise UserNotFoundException()

    if not user.passkeys:
        logger.warning(f"Login attempt for user without passkeys: {request.email}")
        raise UserNotFoundException()

    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {request.email}")
        raise InactiveUserException()

    # Generate authentication options
    options, challenge = get_authentication_options(user.passkeys)

    # Store challenge
    await _store_challenge(request.email, challenge)

    return PasskeyLoginBeginResponse(options=options)


@router.post("/login/complete", response_model=MessageResponse)
async def login_complete(
    request: PasskeyLoginCompleteRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Complete passkey authentication.

    Step 2 of 2 in the login flow.
    Verifies passkey and returns JWT tokens in cookies.

    Args:
        request: Contains email and assertion from browser.
        response: FastAPI response for setting cookies.
        db: Database session.

    Returns:
        Success message.
    """
    # Get stored challenge
    challenge, _ = await _get_and_clear_challenge(request.email)

    # Find user with passkeys
    result = await db.execute(
        select(User)
        .where(User.email == request.email)
        .options(selectinload(User.passkeys))
    )
    user = result.scalars().first()

    if not user or not user.passkeys:
        raise UserNotFoundException()

    # Find the matching passkey by credential ID
    credential_id_bytes = base64url_to_bytes(request.credential["id"])
    matching_passkey = None
    for passkey in user.passkeys:
        if passkey.credential_id == credential_id_bytes:
            matching_passkey = passkey
            break

    if not matching_passkey:
        logger.warning(f"No matching passkey found for: {request.email}")
        raise PasskeyAuthenticationFailedException("Passkey not recognized")

    # Verify the authentication response
    try:
        verified = verify_authentication(
            credential=request.credential,
            expected_challenge=challenge,
            credential_public_key=matching_passkey.public_key,
            credential_current_sign_count=matching_passkey.sign_count,
        )
    except Exception as e:
        logger.warning(f"Passkey authentication verification failed: {e}")
        raise PasskeyAuthenticationFailedException(str(e))

    # Update passkey sign count and last used time
    matching_passkey.sign_count = verified["new_sign_count"]
    matching_passkey.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"User logged in via passkey: {request.email}")

    # Set JWT tokens in cookies
    _set_auth_cookies(response, user.email)

    return MessageResponse(message="Login successful")


# =============================================================================
# Passkey Management Endpoints
# =============================================================================


@router.get("", response_model=PasskeyListResponse)
async def list_passkeys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PasskeyListResponse:
    """
    List all passkeys for the current user.

    Requires authentication.
    """
    result = await db.execute(select(Passkey).where(Passkey.user_id == current_user.id))
    passkeys = result.scalars().all()

    return PasskeyListResponse(
        passkeys=[PasskeyResponse.model_validate(p) for p in passkeys]
    )


@router.patch("/{passkey_id}", response_model=PasskeyResponse)
async def update_passkey(
    passkey_id: int,
    request: PasskeyUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Passkey:
    """
    Update passkey name.

    Requires authentication. User can only update their own passkeys.
    """
    result = await db.execute(
        select(Passkey).where(
            Passkey.id == passkey_id,
            Passkey.user_id == current_user.id,
        )
    )
    passkey = result.scalars().first()

    if not passkey:
        raise PasskeyNotFoundException()

    passkey.name = request.name
    await db.commit()
    await db.refresh(passkey)

    logger.info(f"Passkey {passkey_id} renamed to '{request.name}'")

    return passkey


@router.delete("/{passkey_id}", response_model=MessageResponse)
async def delete_passkey(
    passkey_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Delete a passkey.

    Requires authentication. User must have at least one remaining passkey.
    """
    # Get count of user's passkeys
    result = await db.execute(select(Passkey).where(Passkey.user_id == current_user.id))
    passkeys = result.scalars().all()

    if len(passkeys) <= 1:
        raise PasskeyRegistrationFailedException(
            "Cannot delete your only passkey. Register another passkey first."
        )

    # Find and delete the passkey
    target_passkey = None
    for p in passkeys:
        if p.id == passkey_id:
            target_passkey = p
            break

    if not target_passkey:
        raise PasskeyNotFoundException()

    await db.delete(target_passkey)
    await db.commit()

    logger.info(f"Passkey {passkey_id} deleted for user {current_user.email}")

    return MessageResponse(message="Passkey deleted")


# =============================================================================
# Helper Functions
# =============================================================================


def _set_auth_cookies(response: Response, email: str) -> None:
    """Set JWT access and refresh tokens in HttpOnly cookies."""
    access_token = create_access_token(email)
    refresh_token = create_refresh_token(email)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
