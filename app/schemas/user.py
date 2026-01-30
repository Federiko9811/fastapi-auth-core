"""
User Pydantic schemas for request/response validation.

Note: User registration is handled via passkeys, not passwords.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreatePasskey(BaseModel):
    """
    Schema for user creation during passkey registration.

    Unlike traditional registration, no password is required.
    The user is created when their first passkey is registered.
    """

    email: EmailStr
    display_name: str | None = Field(
        default=None,
        max_length=100,
        description="Optional display name shown in passkey prompts",
    )


class UserResponse(BaseModel):
    """
    Schema for user data in API responses.

    Note: Never include sensitive data in responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    display_name: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime
