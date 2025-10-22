"""
Subscriptions Views - Phase 1 (Database Models Complete)

IMPORTANT: This is a minimal version during Phase 1 implementation.
The full views with new models (PaymentTransaction, ConsultationBooking, etc.)
will be implemented in Phase 2.

Old wallet-based views backed up to: subscriptions/views_old_backup.py
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Q, Sum, Count

from .models import (
    SubscriptionPlan,
    UserSubscription,
    ConsultationVoucher,
    DocumentType,
    DocumentPurchase,
)
from documents.models import LearningMaterial, LearningMaterialPurchase
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    ConsultationVoucherSerializer,
    DocumentTypeSerializer,
    DocumentPurchaseSerializer,
    LearningMaterialSerializer,
    LearningMaterialPurchaseSerializer,
)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subscription plans and user subscriptions
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'plans':
            return SubscriptionPlan.objects.filter(is_active=True)
        return UserSubscription.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'plans':
            return SubscriptionPlanSerializer
        return UserSubscriptionSerializer
    
    @action(detail=False, methods=['get'])
    def plans(self, request):
        """List all active subscription plans"""
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_subscription(self, request):
        """Get current user's subscription details"""
        try:
            subscription = UserSubscription.objects.filter(
                user=request.user
            ).latest('created_at')
            
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response(
                {'detail': 'No active subscription found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def benefits(self, request):
        """Get all available benefits for all subscription plans"""
        plan_id = request.query_params.get('plan_id')
        language = request.query_params.get('language', 'en')  # 'en' or 'sw'
        
        if plan_id:
            # Get benefits for specific plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
                benefits = plan.get_benefits_dict(language=language)
                return Response({
                    'plan_id': plan.id,
                    'plan_name': plan.name,
                    'plan_type': plan.plan_type,
                    'benefits': benefits,
                    'language': language
                })
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'detail': 'Plan not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get benefits for all active plans
            plans = SubscriptionPlan.objects.filter(is_active=True)
            all_benefits = []
            
            for plan in plans:
                all_benefits.append({
                    'plan_id': plan.id,
                    'plan_name': plan.name,
                    'plan_type': plan.plan_type,
                    'price': plan.price,
                    'duration_days': plan.duration_days,
                    'benefits': plan.get_benefits_dict(language=language),
                })
            
            return Response({
                'language': language,
                'plans': all_benefits
            })


class DocumentViewSet(viewsets.ViewSet):
    """ViewSet for document templates"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List all active document types"""
        queryset = DocumentType.objects.filter(is_active=True)
        serializer = DocumentTypeSerializer(queryset, many=True)
        return Response(serializer.data)


class LearningMaterialViewSet(viewsets.ViewSet):
    """ViewSet for learning materials"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List all active learning materials"""
        queryset = LearningMaterial.objects.filter(is_active=True, status='approved')
        serializer = LearningMaterialSerializer(queryset, many=True)
        return Response(serializer.data)
