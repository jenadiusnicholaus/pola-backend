from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Old views (kept for backward compatibility)
from .views import (
    SubscriptionViewSet,
    DocumentViewSet,
    LearningMaterialViewSet
)

# Phase 3: New public-facing views
from .public_views import (
    PricingViewSet,
    CallCreditViewSet,
    ConsultantViewSet,
    ConsultationBookingViewSet,
    PaymentTransactionViewSet,
    EarningsViewSet,
)

# Phase 4: Webhook views
from .webhook_views import azampay_webhook, webhook_health

# User-facing APIs
router = DefaultRouter()

# Old endpoints (backward compatibility)
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'learning', LearningMaterialViewSet, basename='learning')

# Phase 3: New public endpoints
router.register(r'pricing', PricingViewSet, basename='pricing')
router.register(r'call-credits', CallCreditViewSet, basename='call-credit')
router.register(r'consultants', ConsultantViewSet, basename='consultant')
router.register(r'consultations', ConsultationBookingViewSet, basename='consultation')
router.register(r'payments', PaymentTransactionViewSet, basename='payment')
router.register(r'earnings', EarningsViewSet, basename='earnings')

urlpatterns = [
    # User APIs
    path('', include(router.urls)),
    
    # Phase 4: Webhook endpoints
    path('webhooks/azampay/', azampay_webhook, name='azampay-webhook'),
    path('webhooks/health/', webhook_health, name='webhook-health'),
    
    # Note: Admin APIs are now at /api/v1/admin/ (configured in pola_settings/urls.py)
    # Old path 'admin/' removed to avoid confusion
]
