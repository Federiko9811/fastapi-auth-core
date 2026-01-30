"""
WebAuthn utilities for passkey registration and authentication.

This module wraps the py_webauthn library to provide simple functions
for generating options and verifying credentials.
"""

import json
from typing import TYPE_CHECKING

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url, options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.passkey import Passkey


def get_registration_options(
    user_id: bytes,
    user_email: str,
    user_display_name: str | None = None,
    existing_credentials: list["Passkey"] | None = None,
) -> tuple[dict, bytes]:
    """
    Generate WebAuthn registration options for creating a new passkey.

    Args:
        user_id: Unique user identifier (as bytes)
        user_email: User's email address
        user_display_name: Optional display name
        existing_credentials: List of already registered passkeys (to exclude)

    Returns:
        Tuple of (options_dict, challenge_bytes)
        - options_dict: JSON-serializable options for navigator.credentials.create()
        - challenge_bytes: Challenge to store for verification
    """
    # Exclude credentials the user already has
    exclude_credentials = []
    if existing_credentials:
        for cred in existing_credentials:
            exclude_credentials.append(
                PublicKeyCredentialDescriptor(id=cred.credential_id)
            )

    # Generate registration options
    options = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=user_id,
        user_name=user_email,
        user_display_name=user_display_name or user_email,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            # Require resident key (discoverable credential) for passkeys
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )

    # Convert to JSON-serializable dict using webauthn helper
    options_dict = json.loads(options_to_json(options))

    return options_dict, options.challenge


def verify_registration(
    credential: dict,
    expected_challenge: bytes,
    expected_origin: str | None = None,
    expected_rp_id: str | None = None,
) -> dict:
    """
    Verify a WebAuthn registration response.

    Args:
        credential: Credential response from navigator.credentials.create()
        expected_challenge: The challenge that was sent to the client
        expected_origin: Expected origin (defaults to settings)
        expected_rp_id: Expected RP ID (defaults to settings)

    Returns:
        Dictionary with verified credential data:
        - credential_id: bytes
        - public_key: bytes
        - sign_count: int
        - device_type: str ("single_device" or "multi_device")
        - backed_up: bool

    Raises:
        Exception: If verification fails
    """
    verification = verify_registration_response(
        credential=credential,
        expected_challenge=expected_challenge,
        expected_origin=expected_origin or settings.WEBAUTHN_ORIGIN,
        expected_rp_id=expected_rp_id or settings.WEBAUTHN_RP_ID,
    )

    return {
        "credential_id": verification.credential_id,
        "public_key": verification.credential_public_key,
        "sign_count": verification.sign_count,
        "device_type": verification.credential_device_type,
        "backed_up": verification.credential_backed_up,
    }


def get_authentication_options(
    passkeys: list["Passkey"],
) -> tuple[dict, bytes]:
    """
    Generate WebAuthn authentication options for logging in.

    Args:
        passkeys: List of user's registered passkeys

    Returns:
        Tuple of (options_dict, challenge_bytes)
        - options_dict: JSON-serializable options for navigator.credentials.get()
        - challenge_bytes: Challenge to store for verification
    """
    # Build list of allowed credentials
    allow_credentials = []
    for passkey in passkeys:
        transports = None
        if passkey.transports:
            try:
                transport_strs = json.loads(passkey.transports)
                # Convert strings to AuthenticatorTransport enum values
                transports = [
                    AuthenticatorTransport(t)
                    for t in transport_strs
                    if t in [e.value for e in AuthenticatorTransport]
                ]
            except (json.JSONDecodeError, ValueError):
                pass

        allow_credentials.append(
            PublicKeyCredentialDescriptor(
                id=passkey.credential_id,
                transports=transports if transports else None,
            )
        )

    # Generate authentication options
    options = generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    # Convert to JSON-serializable dict using webauthn helper
    options_dict = json.loads(options_to_json(options))

    return options_dict, options.challenge


def verify_authentication(
    credential: dict,
    expected_challenge: bytes,
    credential_public_key: bytes,
    credential_current_sign_count: int,
    expected_origin: str | None = None,
    expected_rp_id: str | None = None,
) -> dict:
    """
    Verify a WebAuthn authentication response.

    Args:
        credential: Assertion response from navigator.credentials.get()
        expected_challenge: The challenge that was sent to the client
        credential_public_key: The stored public key for this credential
        credential_current_sign_count: The stored sign count
        expected_origin: Expected origin (defaults to settings)
        expected_rp_id: Expected RP ID (defaults to settings)

    Returns:
        Dictionary with:
        - new_sign_count: Updated sign count to store

    Raises:
        Exception: If verification fails
    """
    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=expected_challenge,
        expected_origin=expected_origin or settings.WEBAUTHN_ORIGIN,
        expected_rp_id=expected_rp_id or settings.WEBAUTHN_RP_ID,
        credential_public_key=credential_public_key,
        credential_current_sign_count=credential_current_sign_count,
    )

    return {
        "new_sign_count": verification.new_sign_count,
    }


def credential_id_to_base64url(credential_id: bytes) -> str:
    """Convert credential ID bytes to base64url string for comparison."""
    return bytes_to_base64url(credential_id)
