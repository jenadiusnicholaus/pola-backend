"""
Admin API URLs
Routes for user management and permission management
Only accessible by superusers and staff
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import AdminUserManagementViewSet, AdminPermissionManagementViewSet

# Create router for admin APIs
router = DefaultRouter()

# Register viewsets with descriptive base names
router.register(r'users', AdminUserManagementViewSet, basename='admin-users')
router.register(r'permissions', AdminPermissionManagementViewSet, basename='admin-permissions')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
