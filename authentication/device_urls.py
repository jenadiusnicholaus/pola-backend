# authentication/device_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .device_views import (
    UserDeviceViewSet, UserSessionViewSet,
    LoginHistoryViewSet, SecurityAlertViewSet
)

router = DefaultRouter()
router.register(r'devices', UserDeviceViewSet, basename='user-device')
router.register(r'sessions', UserSessionViewSet, basename='user-session')
router.register(r'login-history', LoginHistoryViewSet, basename='login-history')
router.register(r'alerts', SecurityAlertViewSet, basename='security-alert')

urlpatterns = [
    path('', include(router.urls)),
]
