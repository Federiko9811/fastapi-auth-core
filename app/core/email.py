"""
Email service module for sending transactional emails.

Uses fastapi-mail for async SMTP email delivery.
"""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Email configuration
_mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    VALIDATE_CERTS=True,
)

# Lazy-initialized FastMail instance
_fast_mail: FastMail | None = None


def _get_mail_client() -> FastMail:
    """Get or create FastMail client instance."""
    global _fast_mail
    if _fast_mail is None:
        _fast_mail = FastMail(_mail_config)
    return _fast_mail


async def send_otp_email(email: str, otp: str) -> None:
    """
    Send OTP verification code via email.

    Args:
        email: Recipient email address.
        otp: The OTP code to send.
    """
    subject = f"Your verification code: {otp}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
            <h2 style="color: #333;">Passkey Registration Verification</h2>
            <p>You requested to add a new passkey to your account.</p>
            <p>Your verification code is:</p>
            <div style="background-color: #fff; padding: 15px; border-radius: 4px; text-align: center; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #007bff;">{otp}</span>
            </div>
            <p style="color: #666; font-size: 14px;">
                This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.
            </p>
            <p style="color: #666; font-size: 14px;">
                If you didn't request this, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=html_body,
        subtype=MessageType.html,
    )

    try:
        mail_client = _get_mail_client()
        await mail_client.send_message(message)
        logger.info(f"OTP email sent to: {email}")
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        raise
