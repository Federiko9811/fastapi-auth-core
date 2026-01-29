"""
Tests for authentication endpoints.

Uses unique emails for test isolation without database cleanup.
"""

import uuid

from httpx import AsyncClient


def unique_email() -> str:
    """Generate a unique email."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


# Password that meets validation requirements:
# - 8+ characters
# - uppercase letter
# - lowercase letter
# - digit
VALID_PASSWORD = "TestPass123"


async def test_register_user(client: AsyncClient) -> None:
    """Test user registration with valid password."""
    email = unique_email()
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": VALID_PASSWORD},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    assert "password" not in data  # Password should never be in response


async def test_register_weak_password(client: AsyncClient) -> None:
    """Test registration fails with weak password."""
    email = unique_email()
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "weak"},  # Too short, no uppercase/digit
    )

    assert response.status_code == 422  # Validation error
    assert "password" in response.text.lower()


async def test_logout_returns_success(client: AsyncClient) -> None:
    """Test logout endpoint returns success message."""
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"
