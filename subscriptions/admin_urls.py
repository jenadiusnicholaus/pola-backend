"""
Admin API URLs for subscription management
Prefix: /api/v1/subscriptions/admin/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .admin_views import (
    AdminSubscriptionPlanViewSet,
    AdminUserSubscriptionViewSet,
    AdminTransactionViewSet,
    AdminWalletViewSet,
)

# Create router for admin APIs
admin_router = DefaultRouter()
admin_router.register(r'plans', AdminSubscriptionPlanViewSet, basename='admin_plans')
admin_router.register(r'subscriptions', AdminUserSubscriptionViewSet, basename='admin_subscriptions')
admin_router.register(r'transactions', AdminTransactionViewSet, basename='admin_transactions')
admin_router.register(r'wallets', AdminWalletViewSet, basename='admin_wallets')

urlpatterns = admin_router.urls
