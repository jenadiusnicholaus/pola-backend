"""
Hub URLs - Unified API for all hubs (Advocates, Students, Forum)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TopicViewSet, SubtopicViewSet
from .unified_views import (
    HubContentViewSet, HubCommentViewSet, LecturerFollowViewSet,
    MaterialQuestionViewSet, HubMessageViewSet
)

# Legacy router for Legal Education Hub
legacy_router = DefaultRouter()
legacy_router.register(r'legal-education/topics', TopicViewSet, basename='legal-education-topic')
legacy_router.register(r'legal-education/subtopics', SubtopicViewSet, basename='legal-education-subtopic')

# Unified router for all hubs
unified_router = DefaultRouter()
unified_router.register(r'content', HubContentViewSet, basename='hub-content')
unified_router.register(r'comments', HubCommentViewSet, basename='hub-comment')
unified_router.register(r'lecturer-follows', LecturerFollowViewSet, basename='lecturer-follow')
unified_router.register(r'questions', MaterialQuestionViewSet, basename='material-question')
unified_router.register(r'messages', HubMessageViewSet, basename='hub-message')

urlpatterns = [
    # Unified Hub API - Single endpoint for all hubs
    path('', include(unified_router.urls)),
    
    # Legal Education Hub (specialized content)
    path('', include(legacy_router.urls)),
]