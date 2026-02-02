"""
Core configuration module.

Loads settings from environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        PROJECT_NAME: Display name for the application.
        API_V1_STR: URL prefix for API v1 endpoints.
        BACKEND_CORS_ORIGINS: List of allowed CORS origins.
        POSTGRES_*: Database connection settings.
        SECRET_KEY: Secret key for JWT token signing.
        ALGORITHM: Algorithm used for JWT encoding.
        ACCESS_TOKEN_EXPIRE_MINUTES: Lifetime of access tokens in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS: Lifetime of refresh tokens in days.
    """

    PROJECT_NAME: str = "FastAPI Application"
    API_V1_STR: str = "/api/v1"

    # CORS origins - comma-separated string in .env, converted to list
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # WebAuthn / Passkeys settings
    # RP_ID: domain where passkeys are valid (e.g., "example.com")
    # RP_NAME: displayed to user during passkey creation
    # ORIGIN: frontend URL for WebAuthn origin verification
    WEBAUTHN_RP_ID: str = "localhost"
    WEBAUTHN_RP_NAME: str = "FastAPI Auth Core"
    WEBAUTHN_ORIGIN: str = "http://localhost:3000"

    # Redis configuration (for challenge storage)
    REDIS_URL: str = "redis://localhost:6379"

    # Cookie security (set to True in production with HTTPS)
    COOKIE_SECURE: bool = False

    # Rate limiting (requests per IP per window)
    RATE_LIMIT_REQUESTS: int = 100  # Max requests per window
    RATE_LIMIT_WINDOW: int = 60  # Window size in seconds

    # Email Configuration (SMTP)
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "FastAPI Auth"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # OTP Configuration
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3
    OTP_LENGTH: int = 6

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


# Create a single instance to import throughout the application
settings = Settings()
