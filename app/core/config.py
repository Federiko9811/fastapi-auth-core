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
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


# Create a single instance to import throughout the application
settings = Settings()
