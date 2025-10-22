"""
Admin URLs for Hubs Management
Register admin endpoints for topics and subtopics management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import TopicAdminViewSet, SubtopicAdminViewSet

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'topics', TopicAdminViewSet, basename='admin-hub-topics')
router.register(r'subtopics', SubtopicAdminViewSet, basename='admin-hub-subtopics')

urlpatterns = [
    path('', include(router.urls)),
]
