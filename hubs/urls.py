"""
Hub URLs - Educational Content & Social Hubs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TopicViewSet, SubtopicViewSet

router = DefaultRouter()

# Legal Education Hub - Topics & Subtopics
router.register(r'legal-education/topics', TopicViewSet, basename='legal-education-topic')
router.register(r'legal-education/subtopics', SubtopicViewSet, basename='legal-education-subtopic')

# Advocates Hub - To be implemented (posts, documents, messages)
# router.register(r'advocates/posts', AdvocatePostViewSet, basename='advocate-post')

# Students Hub - To be implemented (documents, downloads)
# router.register(r'students/documents', StudentHubDocumentViewSet, basename='student-document')

urlpatterns = [
    path('', include(router.urls)),
]