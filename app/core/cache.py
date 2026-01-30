"""
Redis cache module for temporary data storage.

Used primarily for WebAuthn challenge storage with automatic expiration.
"""

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis client - initialized lazily
_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """
    Get or create Redis client connection.

    Returns:
        Redis async client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False,  # Keep bytes for challenge storage
        )
        logger.info("Redis client initialized")
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


# Challenge storage functions
CHALLENGE_PREFIX = "webauthn:challenge:"
CHALLENGE_EXPIRE_SECONDS = 300  # 5 minutes


async def store_challenge(key: str, challenge: bytes) -> None:
    """
    Store a WebAuthn challenge with automatic expiration.

    Args:
        key: Unique identifier (usually email or user_id)
        challenge: Challenge bytes to store
    """
    client = await get_redis()
    await client.setex(
        f"{CHALLENGE_PREFIX}{key}",
        CHALLENGE_EXPIRE_SECONDS,
        challenge,
    )
    logger.debug(f"Challenge stored for: {key}")


async def get_challenge(key: str) -> bytes | None:
    """
    Retrieve and delete a stored challenge (one-time use).

    Args:
        key: Unique identifier used when storing

    Returns:
        Challenge bytes if found, None otherwise
    """
    client = await get_redis()
    full_key = f"{CHALLENGE_PREFIX}{key}"

    # Get and delete atomically using pipeline
    async with client.pipeline() as pipe:
        pipe.get(full_key)
        pipe.delete(full_key)
        results = await pipe.execute()

    challenge = results[0]
    if challenge:
        logger.debug(f"Challenge retrieved for: {key}")
    return challenge
