"""
Rate limiter middleware using Redis.

Limits requests per IP address using a sliding window algorithm.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.cache import get_redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Rate limit key prefix
RATE_LIMIT_PREFIX = "ratelimit:"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware based on client IP.

    Uses Redis sliding window counter to track requests.
    Returns 429 Too Many Requests when limit is exceeded.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health"]:
            return await call_next(request)

        # Get client IP (handle proxy headers)
        client_ip = self._get_client_ip(request)

        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(client_ip)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP, handling reverse proxies."""
        # Check for forwarded headers (nginx, cloudflare, etc.)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First IP in the list is the original client
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(self, client_ip: str) -> tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Uses Redis sliding window counter.

        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time_seconds)
        """
        try:
            redis = await get_redis()
            key = f"{RATE_LIMIT_PREFIX}{client_ip}"
            window = settings.RATE_LIMIT_WINDOW
            limit = settings.RATE_LIMIT_REQUESTS

            async with redis.pipeline() as pipe:
                # Increment counter and set expiry
                pipe.incr(key)
                pipe.expire(key, window)
                pipe.ttl(key)
                results = await pipe.execute()

            current_count = results[0]
            ttl = results[2] if results[2] > 0 else window

            remaining = max(0, limit - current_count)
            is_allowed = current_count <= limit

            return is_allowed, remaining, ttl
        except Exception as e:
            # If Redis is unavailable, allow the request (fail open)
            logger.warning(f"Rate limit check failed, allowing request: {e}")
            return True, settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW
