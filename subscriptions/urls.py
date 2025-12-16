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
from .webhook_views import azampay_webhook, webhook_health, manual_fulfill_payment

# Phase 5: Call management views
from .call_views import (
    ConsultantListViewSet,
    PhysicalConsultationViewSet,
    CallHistoryViewSet,
)
from .call_management_views import CallManagementViewSet

# Phase 6: Unified payment views
from .payment_views import PaymentViewSet

# User-facing APIs
router = DefaultRouter()

# Register specific paths FIRST (most specific to least specific)
# Phase 3: New public endpoints
router.register(r'pricing', PricingViewSet, basename='pricing')
router.register(r'call-credits', CallCreditViewSet, basename='call-credit')
router.register(r'consultants', ConsultantViewSet, basename='consultant')
router.register(r'consultations', ConsultationBookingViewSet, basename='consultation')
router.register(r'payments', PaymentTransactionViewSet, basename='payment')
router.register(r'earnings', EarningsViewSet, basename='earnings')

# Phase 6: Unified payment API (NEW)
router.register(r'unified-payments', PaymentViewSet, basename='unified-payment')

# Phase 5: Call management endpoints  
router.register(r'call-history', CallHistoryViewSet, basename='call-history')
router.register(r'physical-consultations', PhysicalConsultationViewSet, basename='physical-consultation')

# Old endpoints (backward compatibility)
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'learning', LearningMaterialViewSet, basename='learning')

# Register empty string LAST to avoid catching all routes
# Empty string '' registers the ViewSet directly at /api/v1/subscriptions/
# This makes actions available at: /api/v1/subscriptions/plans/, /api/v1/subscriptions/subscribe/, etc.
router.register(r'', SubscriptionViewSet, basename='subscription')

# Manual paths for call management (to avoid router conflicts)
urlpatterns = [
    # Call management endpoints
    path('calls/initiate/', CallManagementViewSet.as_view({'post': 'initiate'}), name='call-initiate'),
    path('calls/<int:pk>/accept/', CallManagementViewSet.as_view({'post': 'accept'}), name='call-accept'),
    path('calls/<int:pk>/reject/', CallManagementViewSet.as_view({'post': 'reject'}), name='call-reject'),
    path('calls/<int:pk>/end/', CallManagementViewSet.as_view({'post': 'end'}), name='call-end'),
    path('calls/<int:pk>/missed/', CallManagementViewSet.as_view({'post': 'mark_missed'}), name='call-missed'),
    path('calls/consultants/<int:consultant_id>/status/', CallManagementViewSet.as_view({'get': 'consultant_status'}), name='consultant-status'),
    path('calls/check-credits/', CallManagementViewSet.as_view({'post': 'check_credits'}), name='call-check-credits'),
    path('calls/consultants/', ConsultantListViewSet.as_view({'get': 'list'}), name='call-consultants-list'),
    path('calls/consultants/<int:pk>/', ConsultantListViewSet.as_view({'get': 'retrieve'}), name='call-consultants-detail'),
    
    # User APIs
    path('', include(router.urls)),
    
    # Phase 4: Webhook endpoints
    path('webhooks/azampay/', azampay_webhook, name='azampay-webhook'),
    path('webhooks/health/', webhook_health, name='webhook-health'),
    path('webhooks/manual-fulfill/', manual_fulfill_payment, name='manual-fulfill'),  # Testing only
    
    # Note: Admin APIs are now at /api/v1/admin/ (configured in pola_settings/urls.py)
    # Old path 'admin/' removed to avoid confusion
]
