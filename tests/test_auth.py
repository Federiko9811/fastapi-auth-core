"""
Tests for authentication endpoints.

Note: Full WebAuthn testing requires a browser/authenticator.
These tests verify API contracts and error handling.
"""

import uuid

from httpx import AsyncClient


def unique_email() -> str:
    """Generate a unique email."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


async def test_register_begin_returns_options(client: AsyncClient) -> None:
    """Test /passkeys/register/begin returns WebAuthn options."""
    email = unique_email()
    response = await client.post(
        "/api/v1/passkeys/register/begin",
        json={"email": email},
    )

    assert response.status_code == 200
    data = response.json()
    assert "options" in data
    options = data["options"]
    # Verify WebAuthn structure
    assert "challenge" in options
    assert "rp" in options
    assert "user" in options
    assert options["user"]["name"] == email


async def test_login_begin_user_not_found(client: AsyncClient) -> None:
    """Test /passkeys/login/begin returns 404 for non-existent user."""
    email = unique_email()
    response = await client.post(
        "/api/v1/passkeys/login/begin",
        json={"email": email},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_logout_returns_success(client: AsyncClient) -> None:
    """Test logout endpoint returns success message."""
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"


async def test_passkeys_list_requires_auth(client: AsyncClient) -> None:
    """Test /passkeys endpoint requires authentication."""
    response = await client.get("/api/v1/passkeys")

    assert response.status_code == 401
