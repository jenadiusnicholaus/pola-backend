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
from .mention_views import (
    UserMentionViewSet, CommentMentionViewSet, UserPrivacySettingsViewSet
)

# Legacy router for Legal Education Hub
legacy_router = DefaultRouter()
legacy_router.register(r'legal-education/topics', TopicViewSet, basename='legal-education-topic')
legacy_router.register(r'legal-education/subtopics', SubtopicViewSet, basename='legal-education-subtopic')

# Unified router for all hubs
unified_router = DefaultRouter()
unified_router.register(r'content', HubContentViewSet, basename='hub-content')
unified_router.register(r'comments', HubCommentViewSet, basename='hub-comment')  # Now supports mentions
unified_router.register(r'lecturer-follows', LecturerFollowViewSet, basename='lecturer-follow')
unified_router.register(r'questions', MaterialQuestionViewSet, basename='material-question')
unified_router.register(r'messages', HubMessageViewSet, basename='hub-message')

# Mention/Tagging router - Auxiliary endpoints for mentions
mention_router = DefaultRouter()
mention_router.register(r'users', UserMentionViewSet, basename='mention-user')
mention_router.register(r'my-mentions', CommentMentionViewSet, basename='my-mentions')

urlpatterns = [
    # Unified Hub API - Single endpoint for all hubs
    path('', include(unified_router.urls)),
    
    # Mention/Tagging auxiliary endpoints (search users, view mentions, etc.)
    path('mentions/', include(mention_router.urls)),
    
    # Privacy settings (non-router endpoint)
    path('privacy/', UserPrivacySettingsViewSet.as_view({
        'get': 'list',
        'put': 'update',
        'patch': 'update'
    }), name='privacy-settings'),
    
    # Legal Education Hub (specialized content)
    path('', include(legacy_router.urls)),
]