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
import uuid
import logging

from .models import (
    SubscriptionPlan,
    UserSubscription,
    ConsultationVoucher,
    DocumentType,
    DocumentPurchase,
    PaymentTransaction,
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
from .azampay_integration import azampay_client, format_phone_number, detect_mobile_provider

logger = logging.getLogger(__name__)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subscription plans and user subscriptions
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return UserSubscription.objects.none()
        
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
    
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """
        Subscribe to a plan with AzamPay payment
        
        Request body:
        {
            "plan_id": 2,
            "payment_method": "mobile_money",
            "phone_number": "+255712345678"
        }
        """
        plan_id = request.data.get('plan_id')
        payment_method = request.data.get('payment_method', 'mobile_money')
        phone_number = request.data.get('phone_number')
        
        # Validate inputs
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if payment_method == 'mobile_money' and not phone_number:
            return Response(
                {'error': 'phone_number is required for mobile money payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the plan
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Invalid or inactive subscription plan'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already has an active subscription
        existing_subscription = UserSubscription.objects.filter(
            user=request.user,
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        if existing_subscription:
            return Response(
                {
                    'error': 'You already have an active subscription',
                    'current_subscription': {
                        'plan': existing_subscription.plan.name,
                        'end_date': existing_subscription.end_date,
                        'days_remaining': existing_subscription.days_remaining()
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle free trial (no payment required)
        if plan.price == 0 or plan.plan_type == 'free_trial':
            try:
                with db_transaction.atomic():
                    # Create subscription
                    subscription = UserSubscription.objects.create(
                        user=request.user,
                        plan=plan,
                        status='active',
                        end_date=timezone.now() + timedelta(days=plan.duration_days)
                    )
                    
                    # Create transaction record
                    transaction = PaymentTransaction.objects.create(
                        user=request.user,
                        transaction_type='subscription',
                        amount=plan.price,
                        currency=plan.currency,
                        payment_method='free_trial',
                        payment_reference=f"FREE-{uuid.uuid4().hex[:12].upper()}",
                        status='completed',
                        related_subscription=subscription,
                        description=f"Free trial subscription: {plan.name}"
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Free trial activated successfully',
                        'subscription': UserSubscriptionSerializer(subscription).data,
                        'transaction_id': transaction.payment_reference
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                logger.error(f"Error activating free trial: {e}")
                return Response(
                    {'error': 'Failed to activate free trial'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Handle paid subscription
        try:
            with db_transaction.atomic():
                # Format phone number
                formatted_phone = format_phone_number(phone_number)
                
                # Detect provider
                provider = detect_mobile_provider(formatted_phone)
                if provider == 'unknown':
                    return Response(
                        {'error': 'Could not detect mobile money provider from phone number'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Generate external ID
                external_id = f"SUB-{uuid.uuid4().hex[:12].upper()}"
                
                # Create pending subscription
                subscription = UserSubscription.objects.create(
                    user=request.user,
                    plan=plan,
                    status='pending',
                    end_date=timezone.now() + timedelta(days=plan.duration_days)
                )
                
                # Create payment transaction
                transaction = PaymentTransaction.objects.create(
                    user=request.user,
                    transaction_type='subscription',
                    amount=plan.price,
                    currency=plan.currency,
                    payment_method=payment_method,
                    payment_reference=external_id,
                    status='pending',
                    related_subscription=subscription,
                    description=f"Subscription payment: {plan.name}"
                )
                
                # Initiate AzamPay payment
                try:
                    payment_result = azampay_client.mobile_checkout(
                        account_number=formatted_phone,
                        amount=float(plan.price),
                        external_id=external_id,
                        provider=provider
                    )
                    
                    if payment_result.get('success'):
                        # Update transaction with gateway reference
                        transaction.gateway_reference = payment_result.get('transactionId', '')
                        
                        # Check if payment was completed immediately (sandbox mode)
                        if payment_result.get('status') == 'success':
                            transaction.status = 'completed'
                            subscription.status = 'active'
                            subscription.save()
                        
                        transaction.save()
                        
                        return Response({
                            'success': True,
                            'status': 'pending' if payment_result.get('status') != 'success' else 'completed',
                            'message': payment_result.get('message', 'Payment initiated. Please complete payment on your phone.'),
                            'transaction_id': external_id,
                            'azampay_transaction_id': payment_result.get('transactionId'),
                            'payment_details': {
                                'provider': provider,
                                'amount': str(plan.price),
                                'currency': plan.currency,
                                'phone_number': formatted_phone
                            },
                            'subscription_id': subscription.id
                        }, status=status.HTTP_200_OK)
                    else:
                        # Payment initiation failed
                        transaction.status = 'failed'
                        transaction.save()
                        subscription.status = 'cancelled'
                        subscription.save()
                        
                        return Response(
                            {
                                'error': 'Payment initiation failed',
                                'message': payment_result.get('message', 'Unknown error')
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                except Exception as e:
                    logger.error(f"AzamPay error: {e}")
                    transaction.status = 'failed'
                    transaction.save()
                    subscription.status = 'cancelled'
                    subscription.save()
                    
                    return Response(
                        {'error': f'Payment service error: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return Response(
                {'error': 'Failed to process subscription'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def payment_status(self, request):
        """
        Check payment status for a subscription transaction
        
        Query params:
        - transaction_id: Payment reference ID
        """
        transaction_id = request.query_params.get('transaction_id')
        
        if not transaction_id:
            return Response(
                {'error': 'transaction_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get transaction
            transaction = PaymentTransaction.objects.get(
                payment_reference=transaction_id,
                user=request.user
            )
            
            # If already completed, return success
            if transaction.status == 'completed':
                subscription = transaction.related_subscription
                return Response({
                    'transaction_id': transaction_id,
                    'status': 'completed',
                    'subscription_activated': True,
                    'subscription': {
                        'id': subscription.id,
                        'plan': subscription.plan.name,
                        'start_date': subscription.start_date,
                        'end_date': subscription.end_date,
                        'days_remaining': subscription.days_remaining()
                    }
                })
            
            # If pending, check with AzamPay
            if transaction.status == 'pending' and transaction.gateway_reference:
                try:
                    payment_status = azampay_client.check_payment_status(
                        transaction.gateway_reference
                    )
                    
                    if payment_status.get('status') == 'success':
                        # Payment completed - activate subscription
                        with db_transaction.atomic():
                            transaction.status = 'completed'
                            transaction.save()
                            
                            subscription = transaction.related_subscription
                            subscription.status = 'active'
                            subscription.save()
                        
                        return Response({
                            'transaction_id': transaction_id,
                            'status': 'completed',
                            'subscription_activated': True,
                            'subscription': {
                                'id': subscription.id,
                                'plan': subscription.plan.name,
                                'start_date': subscription.start_date,
                                'end_date': subscription.end_date,
                                'days_remaining': subscription.days_remaining()
                            }
                        })
                    
                    elif payment_status.get('status') == 'failed':
                        # Payment failed
                        transaction.status = 'failed'
                        transaction.save()
                        
                        subscription = transaction.related_subscription
                        subscription.status = 'cancelled'
                        subscription.save()
                        
                        return Response({
                            'transaction_id': transaction_id,
                            'status': 'failed',
                            'subscription_activated': False,
                            'message': 'Payment failed'
                        })
                    
                    else:
                        # Still processing
                        return Response({
                            'transaction_id': transaction_id,
                            'status': 'processing',
                            'subscription_activated': False,
                            'message': 'Payment is still being processed'
                        })
                
                except Exception as e:
                    logger.error(f"Error checking payment status: {e}")
                    return Response({
                        'transaction_id': transaction_id,
                        'status': transaction.status,
                        'subscription_activated': False,
                        'message': 'Could not verify payment status'
                    })
            
            # Return current status
            return Response({
                'transaction_id': transaction_id,
                'status': transaction.status,
                'subscription_activated': transaction.status == 'completed'
            })
        
        except PaymentTransaction.DoesNotExist:
            return Response(
                {'error': 'Transaction not found'},
                status=status.HTTP_404_NOT_FOUND
            )


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
