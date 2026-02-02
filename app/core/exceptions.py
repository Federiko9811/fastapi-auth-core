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
    """Exception raised when authentication fails."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication failed",
        )


class InvalidTokenException(HTTPException):
    """Exception raised when token is invalid or expired."""

    def __init__(self, detail: str = "Invalid token") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class UserNotFoundException(HTTPException):
    """Exception raised when user is not found."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


class PasskeyNotFoundException(HTTPException):
    """Exception raised when passkey is not found."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passkey not found",
        )


class PasskeyRegistrationFailedException(HTTPException):
    """Exception raised when passkey registration fails."""

    def __init__(self, detail: str = "Passkey registration failed") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class PasskeyAuthenticationFailedException(HTTPException):
    """Exception raised when passkey authentication fails."""

    def __init__(self, detail: str = "Passkey authentication failed") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ChallengeNotFoundException(HTTPException):
    """Exception raised when WebAuthn challenge is not found or expired."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge not found or expired. Please start the process again.",
        )


class InvalidOTPException(HTTPException):
    """Exception raised when OTP verification fails."""

    def __init__(self, detail: str = "Invalid or expired OTP") -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class OTPRateLimitException(HTTPException):
    """Exception raised when too many OTP attempts."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
        )


class EmailSendException(HTTPException):
    """Exception raised when email sending fails."""

    def __init__(self, detail: str = "Failed to send email") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
