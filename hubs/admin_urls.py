"""
Admin URLs for Hubs Management
Register admin endpoints for topics, subtopics, and hub content management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import TopicAdminViewSet, SubtopicAdminViewSet
from .admin_hub_views import (
    AdminHubContentViewSet,
    AdminHubCommentViewSet,
    AdminHubUserActivityViewSet
)

# Create router
router = DefaultRouter()

# Legal Education Hub admin
router.register(r'topics', TopicAdminViewSet, basename='admin-hub-topics')
router.register(r'subtopics', SubtopicAdminViewSet, basename='admin-hub-subtopics')

# All Hubs content management
router.register(r'hub-content', AdminHubContentViewSet, basename='admin-hub-content')
router.register(r'hub-comments', AdminHubCommentViewSet, basename='admin-hub-comments')
router.register(r'user-activity', AdminHubUserActivityViewSet, basename='admin-user-activity')

urlpatterns = [
    path('', include(router.urls)),
]
