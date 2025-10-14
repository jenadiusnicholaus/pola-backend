from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionViewSet,
    WalletViewSet,
    ConsultationViewSet,
    DocumentViewSet,
    LearningMaterialViewSet
)

# User-facing APIs
router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'learning', LearningMaterialViewSet, basename='learning')

urlpatterns = [
    # User APIs
    path('', include(router.urls)),
    
    # Admin APIs (requires IsAdminUser permission)
    path('admin/', include('subscriptions.admin_urls')),
]
