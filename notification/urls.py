
from django.urls import path, include
from django.conf import settings
from rest_framework import routers
from .views import SendFcmNotification, FcmNotificationViewSet, update_heartbeat
from .notification_views import UserNotificationViewSet

router = routers.DefaultRouter()
router.register(r'send-notification', SendFcmNotification, basename='send')
# NOTE: fcm-token endpoint deprecated - use /api/v1/authentication/devices/register/ instead
router.register(r'notification-view-set', FcmNotificationViewSet, basename='get-notification')
router.register(r'notifications', UserNotificationViewSet, basename='notifications')

API_VERSION =  settings.API_VERSION


urlpatterns = [
    path('', include(router.urls)),
    path('heartbeat/', update_heartbeat, name='heartbeat'),
]
