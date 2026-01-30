"""
Passkey Pydantic schemas for WebAuthn request/response validation.

These schemas handle the complex WebAuthn data structures that need to be
serialized between the server and browser.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =============================================================================
# Registration Schemas
# =============================================================================


class PasskeyRegisterBeginRequest(BaseModel):
    """Request to start passkey registration."""

    email: EmailStr
    display_name: str | None = Field(
        default=None,
        max_length=100,
        description="Optional display name shown in passkey prompts",
    )


class PasskeyRegisterBeginResponse(BaseModel):
    """
    Response containing WebAuthn credential creation options.

    The 'options' field contains JSON that should be passed to
    navigator.credentials.create() in the browser.
    """

    options: dict = Field(
        description="PublicKeyCredentialCreationOptions for the browser"
    )


class PasskeyRegisterCompleteRequest(BaseModel):
    """
    Request to complete passkey registration.

    Contains the credential response from navigator.credentials.create().
    """

    email: EmailStr
    credential: dict = Field(
        description="Credential response from navigator.credentials.create()"
    )
    passkey_name: str | None = Field(
        default=None,
        max_length=100,
        description="User-friendly name for this passkey (e.g., 'My iPhone')",
    )


# =============================================================================
# Authentication Schemas
# =============================================================================


class PasskeyLoginBeginRequest(BaseModel):
    """Request to start passkey authentication."""

    email: EmailStr


class PasskeyLoginBeginResponse(BaseModel):
    """
    Response containing WebAuthn authentication options.

    The 'options' field contains JSON that should be passed to
    navigator.credentials.get() in the browser.
    """

    options: dict = Field(
        description="PublicKeyCredentialRequestOptions for the browser"
    )


class PasskeyLoginCompleteRequest(BaseModel):
    """
    Request to complete passkey authentication.

    Contains the assertion response from navigator.credentials.get().
    """

    email: EmailStr
    credential: dict = Field(
        description="Assertion response from navigator.credentials.get()"
    )


# =============================================================================
# Passkey Management Schemas
# =============================================================================


class PasskeyResponse(BaseModel):
    """Response containing passkey information (for listing)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    device_type: str
    backed_up: bool
    created_at: datetime
    last_used_at: datetime | None


class PasskeyListResponse(BaseModel):
    """Response containing list of user's passkeys."""

    passkeys: list[PasskeyResponse]


class PasskeyUpdateRequest(BaseModel):
    """Request to update passkey metadata."""

    name: str = Field(max_length=100, description="New name for the passkey")
