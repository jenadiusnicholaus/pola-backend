"""
Admin API URL Configuration
All admin management endpoints for comprehensive admin panel
Prefix: /api/v1/admin/

Complete admin control for:
- Hub Management (Topics & Subtopics)
- Subscription Management
- Call Credit Management  
- Consultation Management
- Document Management
- Disbursement Management
- Analytics & Reporting
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .admin_subscription_views import (
    SubscriptionPlanViewSet,
    UserSubscriptionViewSet,
    AdminPaymentTransactionViewSet
)
from .admin_call_credit_views import (
    CallCreditBundleViewSet,
    UserCallCreditViewSet
)
from .admin_consultation_views import (
    PricingConfigurationViewSet,
    ConsultantProfileViewSet,
    ConsultationBookingViewSet
)
from .admin_document_views import (
    LearningMaterialViewSet
)
from .admin_disbursement_views import (
    AdminDisbursementViewSet as DisbursementViewSet,
    AdminEarningsManagementViewSet as EarningsManagementViewSet
)
from .admin_analytics_views import (
    dashboard_overview,
    revenue_analytics,
    user_analytics,
    platform_health
)
from authentication.admin_views import AdminUserManagementViewSet

# Create router
router = DefaultRouter()

# ===== USER MANAGEMENT ===== 
router.register(r'users', AdminUserManagementViewSet, basename='admin-users')

# ===== SUBSCRIPTION MANAGEMENT =====
router.register(r'subscriptions/plans', SubscriptionPlanViewSet, basename='admin-subscription-plans')
router.register(r'subscriptions/users', UserSubscriptionViewSet, basename='admin-user-subscriptions')
router.register(r'subscriptions/transactions', AdminPaymentTransactionViewSet, basename='admin-transactions')

# ===== CALL CREDIT MANAGEMENT =====
router.register(r'call-credits/bundles', CallCreditBundleViewSet, basename='admin-call-bundles')
router.register(r'call-credits/users', UserCallCreditViewSet, basename='admin-user-credits')

# ===== CONSULTATION MANAGEMENT =====
router.register(r'consultations/pricing', PricingConfigurationViewSet, basename='admin-pricing')
router.register(r'consultations/consultants', ConsultantProfileViewSet, basename='admin-consultants')
router.register(r'consultations/bookings', ConsultationBookingViewSet, basename='admin-bookings')

# ===== DOCUMENT MANAGEMENT =====
router.register(r'documents/materials', LearningMaterialViewSet, basename='admin-materials')

# ===== DISBURSEMENT MANAGEMENT =====
router.register(r'disbursements', DisbursementViewSet, basename='admin-disbursements')
router.register(r'earnings', EarningsManagementViewSet, basename='admin-earnings-management')

# URL Patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # ===== HUB MANAGEMENT =====
    path('hubs/', include('hubs.admin_urls')),
    
    # ===== ANALYTICS & REPORTING =====
    path('analytics/dashboard/', dashboard_overview, name='admin-dashboard'),
    path('analytics/revenue/', revenue_analytics, name='admin-revenue'),
    path('analytics/users/', user_analytics, name='admin-users-analytics'),
    path('analytics/health/', platform_health, name='admin-health'),
]

