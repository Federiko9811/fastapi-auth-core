"""
OTP (One-Time Password) generation and verification module.

Uses Redis for secure storage with automatic expiration.
"""

import hashlib
import secrets

from app.core.cache import get_redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis key prefixes
OTP_PREFIX = "otp:"
OTP_ATTEMPTS_PREFIX = "otp:attempts:"
OTP_VERIFIED_PREFIX = "otp:verified:"


def generate_otp() -> str:
    """
    Generate a cryptographically secure OTP code.

    Returns:
        String of digits with length defined by settings.OTP_LENGTH.
    """
    # Use secrets for cryptographic randomness
    max_value = 10**settings.OTP_LENGTH - 1
    otp = secrets.randbelow(max_value + 1)
    return str(otp).zfill(settings.OTP_LENGTH)


def _hash_otp(otp: str) -> str:
    """Hash OTP for secure storage."""
    return hashlib.sha256(otp.encode()).hexdigest()


async def store_otp(email: str, otp: str) -> None:
    """
    Store hashed OTP in Redis with automatic expiration.

    Args:
        email: User's email address (used as key).
        otp: Plain text OTP code.
    """
    client = await get_redis()
    otp_hash = _hash_otp(otp)
    expire_seconds = settings.OTP_EXPIRE_MINUTES * 60

    # Store hashed OTP
    await client.setex(f"{OTP_PREFIX}{email}", expire_seconds, otp_hash)

    # Reset attempt counter
    await client.delete(f"{OTP_ATTEMPTS_PREFIX}{email}")

    logger.debug(f"OTP stored for: {email}")


async def verify_otp(email: str, otp: str) -> bool:
    """
    Verify OTP and invalidate it (one-time use).

    Args:
        email: User's email address.
        otp: OTP code to verify.

    Returns:
        True if OTP is valid, False otherwise.
    """
    client = await get_redis()
    key = f"{OTP_PREFIX}{email}"
    attempts_key = f"{OTP_ATTEMPTS_PREFIX}{email}"

    # Check attempt count
    attempts = await client.get(attempts_key)
    if attempts and int(attempts) >= settings.OTP_MAX_ATTEMPTS:
        logger.warning(f"OTP max attempts exceeded for: {email}")
        return False

    # Increment attempt counter (15 min TTL)
    await client.incr(attempts_key)
    await client.expire(attempts_key, 900)

    # Get stored hash
    stored_hash = await client.get(key)
    if not stored_hash:
        logger.debug(f"OTP not found or expired for: {email}")
        return False

    # Compare hashes
    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode()

    if _hash_otp(otp) != stored_hash:
        logger.debug(f"OTP mismatch for: {email}")
        return False

    # Valid OTP - delete it (one-time use) and mark as verified
    await client.delete(key)
    await client.delete(attempts_key)

    # Store verification flag (valid for challenge duration)
    verified_key = f"{OTP_VERIFIED_PREFIX}{email}"
    await client.setex(verified_key, 300, "1")  # 5 minutes to complete registration

    logger.info(f"OTP verified for: {email}")
    return True


async def is_otp_verified(email: str) -> bool:
    """
    Check if OTP was recently verified for this email.

    Args:
        email: User's email address.

    Returns:
        True if OTP was verified within the verification window.
    """
    client = await get_redis()
    verified = await client.get(f"{OTP_VERIFIED_PREFIX}{email}")
    return verified is not None


async def clear_otp_verification(email: str) -> None:
    """Clear OTP verification flag after successful passkey registration."""
    client = await get_redis()
    await client.delete(f"{OTP_VERIFIED_PREFIX}{email}")
    logger.debug(f"OTP verification cleared for: {email}")


async def check_rate_limit(email: str) -> bool:
    """
    Check if user has exceeded OTP attempt limit.

    Args:
        email: User's email address.

    Returns:
        True if within limits, False if rate limited.
    """
    client = await get_redis()
    attempts = await client.get(f"{OTP_ATTEMPTS_PREFIX}{email}")
    if attempts and int(attempts) >= settings.OTP_MAX_ATTEMPTS:
        return False
    return True
