"""
Token and message response schemas.
"""

from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT token payload data."""

    sub: str  # Subject (user email)
    exp: int  # Expiration timestamp
    type: str  # Token type: "access" or "refresh"


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str
