"""
Dedicated URL configuration for consultant-related endpoints
Provides shorter, cleaner URLs for consultant operations
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .public_views import ConsultantViewSet

# Create a dedicated router for consultants only
router = DefaultRouter()
router.register(r'', ConsultantViewSet, basename='consultant')

urlpatterns = [
    path('', include(router.urls)),
]
