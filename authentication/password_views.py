"""
Forgot / reset password API views.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView

from .email_utils import send_password_reset_otp_email
from .password_reset_models import PasswordResetOTP
from .password_serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

GENERIC_RESET_MESSAGE = (
    'If an account exists with that email, a password reset code has been sent.'
)


class PasswordResetThrottle(throttling.AnonRateThrottle):
    scope = 'password_reset'


class PasswordResetRequestView(APIView):
    """
    POST /authentication/reset-password/
    Body: { "email": "user@example.com" }
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    @swagger_auto_schema(
        operation_description='Request a password reset OTP by email',
        request_body=PasswordResetRequestSerializer,
        responses={200: openapi.Response(description='Generic success message')},
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        response_data = {'message': GENERIC_RESET_MESSAGE}

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            ttl = getattr(settings, 'PASSWORD_RESET_OTP_TTL_MINUTES', 15)
            _, raw_otp = PasswordResetOTP.create_for_user(user, ttl_minutes=ttl)
            sent = send_password_reset_otp_email(user.email, raw_otp, ttl_minutes=ttl)
            if settings.DEBUG:
                # Helpful for local/emulator testing without SMTP
                response_data['debug_otp'] = raw_otp
                response_data['email_sent'] = sent
                logger.warning('DEBUG password reset OTP for %s: %s', user.email, raw_otp)

        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetVerifyView(APIView):
    """
    POST /authentication/verify-reset-otp/
    Body: { "email": "...", "otp": "123456" }
    Validates OTP without consuming it so the user can then set a new password.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    @swagger_auto_schema(
        operation_description='Verify password reset OTP before setting a new password',
        request_body=PasswordResetVerifySerializer,
        responses={
            200: openapi.Response(description='OTP is valid'),
            400: 'Invalid OTP',
        },
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response(
                {'detail': 'Invalid or expired reset code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset = (
            PasswordResetOTP.objects.filter(
                user=user,
                is_used=False,
                expires_at__gte=timezone.now(),
            )
            .order_by('-created_at')
            .first()
        )
        if not reset or not reset.check_otp(otp):
            return Response(
                {'detail': 'Invalid or expired reset code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'message': 'OTP verified successfully. You can set a new password.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    POST /authentication/confirm-reset-password/
    Body: {
      "email": "...",
      "otp": "123456",
      "new_password": "...",
      "new_password_confirm": "..."
    }
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    @swagger_auto_schema(
        operation_description='Confirm password reset with OTP and set a new password',
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(description='Password reset successful'),
            400: 'Invalid OTP or validation error',
        },
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return Response(
                {'detail': 'Invalid or expired reset code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset = (
            PasswordResetOTP.objects.filter(
                user=user,
                is_used=False,
                expires_at__gte=timezone.now(),
            )
            .order_by('-created_at')
            .first()
        )
        if not reset or not reset.verify(otp):
            return Response(
                {'detail': 'Invalid or expired reset code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=['password'])
        self._blacklist_user_tokens(user)

        return Response(
            {'message': 'Password has been reset successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _blacklist_user_tokens(user):
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            for token in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            logger.exception('Failed to blacklist tokens after password reset for %s', user.email)
