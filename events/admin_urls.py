"""
Admin URLs for Event Management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import EventAdminViewSet

router = DefaultRouter()
router.register(r"events", EventAdminViewSet, basename="admin-events")

urlpatterns = [
    path("", include(router.urls)),
]
