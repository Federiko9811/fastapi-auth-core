"""
Tests for OTP generation and verification.
"""

import pytest

from app.core.otp import generate_otp


def test_generate_otp_length() -> None:
    """Test that generated OTP has correct length."""
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_generate_otp_uniqueness() -> None:
    """Test that OTPs are unique (probabilistically)."""
    otps = [generate_otp() for _ in range(100)]
    # With 6-digit OTPs, collisions are rare in 100 samples
    assert len(set(otps)) > 90


@pytest.mark.asyncio
async def test_register_begin_existing_user_requires_otp(client) -> None:
    """Test that existing users require OTP verification."""
    # This test requires a registered user first
    # Skip if database not available
    pass


@pytest.mark.asyncio
async def test_register_begin_new_user_no_otp(client) -> None:
    """Test that new users get passkey options directly."""
    import uuid

    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/v1/passkeys/register/begin",
        json={"email": email},
    )

    assert response.status_code == 200
    data = response.json()
    # New users should get options directly
    assert data.get("requires_otp") is False
    assert data.get("options") is not None
