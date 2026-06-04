"""
Document Template URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentTemplateViewSet, UserDocumentViewSet, DocumentContentAdminViewSet

router = DefaultRouter()
router.register(r'templates', DocumentTemplateViewSet, basename='document-template')
router.register(r'documents', UserDocumentViewSet, basename='user-document')
router.register(r'admin/document-content', DocumentContentAdminViewSet, basename='document-content-admin')

urlpatterns = [
    path('', include(router.urls)),
]
