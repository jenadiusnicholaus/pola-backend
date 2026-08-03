"""
Email helpers for authentication flows.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_password_reset_otp_email(email: str, otp: str, ttl_minutes: int = 15) -> bool:
    """Send password-reset OTP email. Returns True if send_mail succeeded."""
    subject = 'POLA Password Reset Code'
    message = (
        'You requested a password reset for your POLA account.\n\n'
        f'Your reset code is: {otp}\n\n'
        f'This code expires in {ttl_minutes} minutes.\n'
        'If you did not request this, you can ignore this email.\n'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pola.co.tz')

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info('Password reset OTP email sent to %s', email)
        return True
    except Exception:
        logger.exception('Failed to send password reset OTP email to %s', email)
        # Still log OTP in DEBUG so local testing works without SMTP
        if settings.DEBUG:
            logger.warning('DEBUG password reset OTP for %s: %s', email, otp)
        return False
