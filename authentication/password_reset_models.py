"""
Password reset OTP model.
"""
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class PasswordResetOTP(models.Model):
    """One-time password for forgot-password flow."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_otps',
    )
    otp = models.CharField(
        max_length=6,
        blank=True,
        default='',
        help_text='Plain OTP code (also stored hashed in otp_hash)',
    )
    otp_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used', '-created_at']),
        ]

    def __str__(self):
        return f'Password reset OTP for {self.user.email} ({self.expires_at})'

    @staticmethod
    def hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode('utf-8')).hexdigest()

    @classmethod
    def generate_otp(cls) -> str:
        return f'{secrets.randbelow(1_000_000):06d}'

    @classmethod
    def create_for_user(cls, user, ttl_minutes: int = 15):
        """Invalidate previous unused OTPs and create a new one. Returns (instance, raw_otp)."""
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        raw_otp = cls.generate_otp()
        instance = cls.objects.create(
            user=user,
            otp=raw_otp,
            otp_hash=cls.hash_otp(raw_otp),
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )
        return instance, raw_otp

    def is_valid(self) -> bool:
        return (
            not self.is_used
            and self.attempts < 5
            and timezone.now() <= self.expires_at
        )

    def check_otp(self, otp: str) -> bool:
        """Validate OTP without consuming it. Failed attempts are counted."""
        if not self.is_valid():
            return False
        if self.otp_hash != self.hash_otp(otp.strip()):
            self.attempts += 1
            self.save(update_fields=['attempts'])
            return False
        return True

    def verify(self, otp: str) -> bool:
        self.attempts += 1
        self.save(update_fields=['attempts'])
        if not self.is_valid():
            return False
        if self.otp_hash != self.hash_otp(otp):
            return False
        self.is_used = True
        self.save(update_fields=['is_used'])
        return True
