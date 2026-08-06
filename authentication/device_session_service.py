"""
Single-device session enforcement helpers.
"""
import logging

from django.utils import timezone

from .device_models import UserDevice, UserSession

logger = logging.getLogger(__name__)


def make_device_current(user, device):
    """
    Promote ``device`` to the sole current device for ``user``.

    - Demotes other current devices
    - Terminates their active sessions
    - Sends FCM force_logout to those devices (best-effort)
    """
    old_devices = list(
        UserDevice.objects.filter(
            user=user,
            is_current_device=True,
            is_active=True,
        ).exclude(pk=device.pk)
    )

    for old in old_devices:
        _send_force_logout(old)

    if old_devices:
        UserDevice.objects.filter(
            user=user,
            is_current_device=True,
        ).exclude(pk=device.pk).update(is_current_device=False)

        UserSession.objects.filter(
            user=user,
            status='active',
        ).exclude(device=device).update(
            status='terminated',
            logout_time=timezone.now(),
        )

    update_fields = []
    if not device.is_current_device:
        device.is_current_device = True
        update_fields.append('is_current_device')
    if not device.is_verified:
        device.is_verified = True
        update_fields.append('is_verified')
    if update_fields:
        device.save(update_fields=update_fields)

    logger.info(
        '✅ Device %s is now the sole current device for user %s '
        '(demoted %s other device(s))',
        device.device_id,
        user.email,
        len(old_devices),
    )
    return old_devices


def _send_force_logout(device):
    """Push a force_logout notification to a demoted device."""
    if not device.fcm_token:
        return
    try:
        from notification.notification_service import NotificationService

        fcm = NotificationService._get_fcm_instance()
        if not fcm:
            return

        data = {
            'type': 'force_logout',
            'reason': 'device_replaced',
            'message': 'Your account was signed in on another device.',
        }
        status_code, _ = fcm.send_notification(
            device.fcm_token,
            'Signed out',
            'Your account was signed in on another device.',
            data,
        )
        logger.info(
            '📤 force_logout FCM to device %s → %s',
            device.device_id[:12],
            status_code,
        )
    except Exception:
        logger.exception(
            'Failed to send force_logout FCM to device %s',
            device.device_id,
        )
