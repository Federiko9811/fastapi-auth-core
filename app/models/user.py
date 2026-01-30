"""
User model for the application.

Note: This model uses passwordless authentication via WebAuthn passkeys.
The hashed_password field has been removed - users authenticate with passkeys only.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.passkey import Passkey


class User(Base):
    """
    User account model.

    Attributes:
        email: Unique email address (used as username)
        display_name: Optional display name shown in passkey prompts
        is_active: Account active status
        is_admin: Admin privileges flag
        passkeys: List of registered WebAuthn credentials
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Relationship to passkeys (one user can have multiple passkeys)
    passkeys: Mapped[list["Passkey"]] = relationship(
        "Passkey", back_populates="user", cascade="all, delete-orphan"
    )
