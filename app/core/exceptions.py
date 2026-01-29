"""
Custom exception classes for the application.

Provides centralized, reusable exceptions with consistent HTTP responses.
"""

from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    """Exception raised when authentication credentials are invalid."""

    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InactiveUserException(HTTPException):
    """Exception raised when user account is inactive."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )


class EmailAlreadyExistsException(HTTPException):
    """Exception raised when email is already registered."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )


class InvalidCredentialsException(HTTPException):
    """Exception raised when login credentials are incorrect."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )


class InvalidTokenException(HTTPException):
    """Exception raised when token is invalid or expired."""

    def __init__(self, detail: str = "Invalid token") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )
