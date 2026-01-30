"""
Passkey model for storing WebAuthn credentials.

Each user can have multiple passkeys (e.g., phone, laptop, security key).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Passkey(Base):
    """
    Stores WebAuthn credential data for passwordless authentication.

    Attributes:
        credential_id: Unique identifier from authenticator (used to identify passkey)
        public_key: Public key bytes for signature verification
        sign_count: Counter to detect cloned authenticators (anti-replay)
        device_type: "single_device" or "multi_device" (synced passkeys)
        backed_up: Whether the passkey is backed up to cloud
        transports: JSON array of transport hints (usb, nfc, ble, internal, hybrid)
        name: User-assigned friendly name (e.g., "iPhone di Federico")
        last_used_at: Last successful authentication timestamp
    """

    __tablename__ = "passkeys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # WebAuthn credential data
    credential_id: Mapped[bytes] = mapped_column(
        LargeBinary, unique=True, nullable=False, index=True
    )
    public_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Credential metadata (from authenticator)
    device_type: Mapped[str] = mapped_column(
        String(20), default="single_device", nullable=False
    )
    backed_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transports: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array

    # User-facing metadata
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="passkeys")
