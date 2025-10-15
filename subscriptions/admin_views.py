"""
Admin-only views for managing subscriptions, plans, and transactions
Restricted to superusers and staff with appropriate permissions
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Count, Sum, Q
from datetime import timedelta
from decimal import Decimal

from .models import (
    SubscriptionPlan,
    UserSubscription,
    PaymentTransaction,
    ConsultantEarnings,
    UploaderEarnings,
)
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    # PaymentTransactionSerializer,  # TODO: Create in Phase 2
)
from authentication.models import PolaUser


class AdminSubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing subscription plans
    
    Endpoints:
    - GET /admin/plans/ - List all plans
    - POST /admin/plans/ - Create new plan
    - GET /admin/plans/{id}/ - Get plan details
    - PUT/PATCH /admin/plans/{id}/ - Update plan
    - DELETE /admin/plans/{id}/ - Delete plan
    - POST /admin/plans/{id}/activate/ - Activate plan
    - POST /admin/plans/{id}/deactivate/ - Deactivate plan
    - GET /admin/plans/statistics/ - Get plan statistics
    """
    permission_classes = [IsAdminUser]
    serializer_class = SubscriptionPlanSerializer
    queryset = SubscriptionPlan.objects.all()
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get subscription plan statistics"""
        plans = SubscriptionPlan.objects.all()
        
        stats = []
        for plan in plans:
            subscriptions = UserSubscription.objects.filter(plan=plan)
            
            stats.append({
                'plan_id': plan.id,
                'plan_name': plan.name,
                'plan_type': plan.plan_type,
                'price': float(plan.price),
                'total_subscriptions': subscriptions.count(),
                'active_subscriptions': subscriptions.filter(status='active').count(),
                'expired_subscriptions': subscriptions.filter(status='expired').count(),
                'cancelled_subscriptions': subscriptions.filter(status='cancelled').count(),
                'total_revenue': float(
                    PaymentTransaction.objects.filter(
                        transaction_type='subscription',
                        related_subscription__plan=plan,
                        status='completed'
                    ).aggregate(total=Sum('amount'))['total'] or 0
                ),
                'is_active': plan.is_active
            })
        
        return Response({
            'statistics': stats,
            'total_plans': plans.count(),
            'active_plans': plans.filter(is_active=True).count()
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a subscription plan"""
        plan = self.get_object()
        plan.is_active = True
        plan.save()
        
        return Response({
            'message': f'Plan "{plan.name}" activated successfully',
            'plan': SubscriptionPlanSerializer(plan).data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a subscription plan"""
        plan = self.get_object()
        plan.is_active = False
        plan.save()
        
        return Response({
            'message': f'Plan "{plan.name}" deactivated successfully',
            'plan': SubscriptionPlanSerializer(plan).data
        })


class AdminUserSubscriptionViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing user subscriptions
    
    Endpoints:
    - GET /admin/subscriptions/ - List all subscriptions (with filters)
    - GET /admin/subscriptions/{id}/ - Get subscription details
    - PUT/PATCH /admin/subscriptions/{id}/ - Update subscription
    - POST /admin/subscriptions/{id}/cancel/ - Cancel subscription
    - POST /admin/subscriptions/{id}/extend/ - Extend subscription
    - POST /admin/subscriptions/{id}/activate/ - Activate subscription
    - POST /admin/subscriptions/create/ - Create subscription for user
    - GET /admin/subscriptions/statistics/ - Get subscription statistics
    """
    permission_classes = [IsAdminUser]
    serializer_class = UserSubscriptionSerializer
    queryset = UserSubscription.objects.all().select_related('user', 'plan')
    
    def get_queryset(self):
        """Filter subscriptions based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by plan
        plan_id = self.request.query_params.get('plan_id')
        if plan_id:
            queryset = queryset.filter(plan_id=plan_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by email
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(user__email__icontains=email)
        
        # Filter by trial
        is_trial = self.request.query_params.get('is_trial')
        if is_trial == 'true':
            queryset = queryset.filter(plan__plan_type='free_trial')
        elif is_trial == 'false':
            queryset = queryset.exclude(plan__plan_type='free_trial')
        
        # Filter expiring soon
        expiring_days = self.request.query_params.get('expiring_in_days')
        if expiring_days:
            days = int(expiring_days)
            expiring_date = timezone.now() + timedelta(days=days)
            queryset = queryset.filter(
                end_date__lte=expiring_date,
                status='active'
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get subscription statistics"""
        all_subs = UserSubscription.objects.all()
        
        stats = {
            'total_subscriptions': all_subs.count(),
            'active_subscriptions': all_subs.filter(status='active').count(),
            'expired_subscriptions': all_subs.filter(status='expired').count(),
            'cancelled_subscriptions': all_subs.filter(status='cancelled').count(),
            'trial_subscriptions': all_subs.filter(plan__plan_type='free_trial').count(),
            'paid_subscriptions': all_subs.exclude(plan__plan_type='free_trial').count(),
            'expiring_today': all_subs.filter(
                end_date__date=timezone.now().date(),
                status='active'
            ).count(),
            'expiring_this_week': all_subs.filter(
                end_date__lte=timezone.now() + timedelta(days=7),
                end_date__gte=timezone.now(),
                status='active'
            ).count(),
            'auto_renew_enabled': all_subs.filter(auto_renew=True, status='active').count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a user's subscription"""
        subscription = self.get_object()
        reason = request.data.get('reason', 'Admin cancellation')
        
        subscription.cancel_subscription()
        
        return Response({
            'message': f'Subscription cancelled for {subscription.user.email}',
            'reason': reason,
            'subscription': UserSubscriptionSerializer(subscription).data
        })
    
    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """Extend a user's subscription"""
        subscription = self.get_object()
        days = request.data.get('days')
        reason = request.data.get('reason', 'Admin extension')
        
        if not days:
            return Response(
                {'error': 'days parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            days = int(days)
            if days <= 0:
                raise ValueError("Days must be positive")
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.extend_subscription(days)
        
        return Response({
            'message': f'Subscription extended by {days} days for {subscription.user.email}',
            'reason': reason,
            'new_end_date': subscription.end_date.isoformat(),
            'subscription': UserSubscriptionSerializer(subscription).data
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a subscription"""
        subscription = self.get_object()
        subscription.activate_subscription()
        
        return Response({
            'message': f'Subscription activated for {subscription.user.email}',
            'subscription': UserSubscriptionSerializer(subscription).data
        })
    
    @action(detail=False, methods=['post'])
    def create_for_user(self, request):
        """Create subscription for a specific user"""
        user_id = request.data.get('user_id')
        plan_id = request.data.get('plan_id')
        auto_renew = request.data.get('auto_renew', False)
        
        if not user_id or not plan_id:
            return Response(
                {'error': 'user_id and plan_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = PolaUser.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except (PolaUser.DoesNotExist, SubscriptionPlan.DoesNotExist) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already has subscription
        if hasattr(user, 'subscription'):
            return Response(
                {
                    'error': f'User {user.email} already has a subscription',
                    'existing_subscription': UserSubscriptionSerializer(user.subscription).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create subscription
        end_date = timezone.now() + timedelta(days=plan.duration_days)
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            end_date=end_date,
            auto_renew=auto_renew
        )
        
        return Response({
            'message': f'Subscription created for {user.email}',
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)


class AdminPaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for viewing and managing payment transactions (NEW - No wallet system)
    
    Endpoints:
    - GET /admin/transactions/ - List all transactions (with filters)
    - GET /admin/transactions/{id}/ - Get transaction details
    - POST /admin/transactions/{id}/refund/ - Process refund
    - POST /admin/transactions/{id}/complete/ - Mark as completed
    - POST /admin/transactions/{id}/fail/ - Mark as failed
    - POST /admin/transactions/{id}/cancel/ - Cancel transaction
    - GET /admin/transactions/statistics/ - Get transaction statistics
    
    Note: Refunds now go back to payment method (AzamPay), not wallet
    """
    permission_classes = [IsAdminUser]
    # serializer_class = PaymentTransactionSerializer  # TODO: Create in Phase 2
    queryset = PaymentTransaction.objects.all().select_related('user')
    
    def get_queryset(self):
        """Filter transactions based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by email
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(user__email__icontains=email)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get payment transaction statistics (NO wallet system)"""
        all_transactions = PaymentTransaction.objects.all()
        completed = all_transactions.filter(status='completed')
        
        # Revenue by transaction type
        revenue_by_type = {}
        for trans_type, _ in PaymentTransaction.TRANSACTION_TYPES:
            revenue = completed.filter(
                transaction_type=trans_type
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_by_type[trans_type] = float(revenue)
        
        stats = {
            'total_transactions': all_transactions.count(),
            'completed_transactions': completed.count(),
            'pending_transactions': all_transactions.filter(status='pending').count(),
            'failed_transactions': all_transactions.filter(status='failed').count(),
            'refunded_transactions': all_transactions.filter(status='refunded').count(),
            'total_revenue': float(
                completed.filter(
                    transaction_type__in=['subscription', 'consultation', 
                                         'document', 'material', 'call_credit']
                ).aggregate(total=Sum('amount'))['total'] or 0
            ),
            'total_refunds': float(
                completed.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or 0
            ),
            'revenue_by_type': revenue_by_type,
            'payment_methods': self._get_payment_method_stats(completed),
        }
        
        return Response(stats)
    
    def _get_payment_method_stats(self, completed_transactions):
        """Get statistics by payment method"""
        stats = {}
        for method, _ in PaymentTransaction.PAYMENT_METHODS:
            amount = completed_transactions.filter(
                payment_method=method
            ).aggregate(total=Sum('amount'))['total'] or 0
            count = completed_transactions.filter(payment_method=method).count()
            stats[method] = {
                'total_amount': float(amount),
                'transaction_count': count
            }
        return stats
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Process a refund for a transaction (NO wallet - refund to payment method)
        
        Note: This creates a refund transaction record. Actual refund processing
        through AzamPay should be implemented in Phase 2.
        """
        transaction = self.get_object()
        reason = request.data.get('reason', 'Admin refund')
        refund_amount = request.data.get('amount')
        
        # Validation
        if transaction.status != 'completed':
            return Response(
                {'error': 'Can only refund completed transactions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if transaction.transaction_type == 'refund':
            return Response(
                {'error': 'Cannot refund a refund transaction'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine refund amount
        if refund_amount:
            try:
                refund_amount = Decimal(str(refund_amount))
                if refund_amount <= 0 or refund_amount > transaction.amount:
                    raise ValueError("Invalid refund amount")
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            refund_amount = transaction.amount
        
        with db_transaction.atomic():
            # Create refund transaction record
            refund_transaction = PaymentTransaction.objects.create(
                user=transaction.user,
                transaction_type='refund',
                amount=refund_amount,
                currency=transaction.currency,
                payment_method=transaction.payment_method,
                payment_reference=f'REFUND-{transaction.payment_reference}',
                gateway_reference=transaction.gateway_reference,
                status='completed',
                description=f'Refund for {transaction.payment_reference}: {reason}',
            )
            
            # Update original transaction status if full refund
            if refund_amount == transaction.amount:
                transaction.status = 'refunded'
                transaction.save()
        
        return Response({
            'message': f'Refund of {refund_amount} TZS processed successfully',
            'reason': reason,
            'note': 'Refund will be processed through payment gateway (AzamPay)',
            'original_transaction': {
                'id': transaction.id,
                'reference': transaction.payment_reference,
                'amount': float(transaction.amount),
                'status': transaction.status,
            },
            'refund_transaction': {
                'id': refund_transaction.id,
                'reference': refund_transaction.payment_reference,
                'amount': float(refund_transaction.amount),
            }
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark transaction as completed"""
        transaction = self.get_object()
        
        if transaction.status == 'completed':
            return Response(
                {'error': 'Transaction already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.status = 'completed'
        transaction.save()
        
        return Response({
            'message': f'Transaction {transaction.payment_reference} marked as completed',
            'transaction': {
                'id': transaction.id,
                'reference': transaction.payment_reference,
                'amount': float(transaction.amount),
                'status': transaction.status,
            }
        })
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """Mark transaction as failed"""
        transaction = self.get_object()
        reason = request.data.get('reason', 'Admin marked as failed')
        
        transaction.status = 'failed'
        transaction.description += f'\nFailed: {reason}'
        transaction.save()
        
        return Response({
            'message': f'Transaction {transaction.payment_reference} marked as failed',
            'reason': reason,
            'transaction': {
                'id': transaction.id,
                'reference': transaction.payment_reference,
                'amount': float(transaction.amount),
                'status': transaction.status,
            }
        })
    
    @action(detail=True, methods=['post'])
    def cancel_transaction(self, request, pk=None):
        """Cancel a transaction"""
        transaction = self.get_object()
        reason = request.data.get('reason', 'Admin cancellation')
        
        if transaction.status == 'completed':
            return Response(
                {'error': 'Cannot cancel completed transaction. Use refund instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.status = 'cancelled'
        transaction.description += f'\nCancelled: {reason}'
        transaction.save()
        
        return Response({
            'message': f'Transaction {transaction.payment_reference} cancelled',
            'reason': reason,
            'transaction': {
                'id': transaction.id,
                'reference': transaction.payment_reference,
                'amount': float(transaction.amount),
                'status': transaction.status,
            }
        })


class AdminEarningsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for viewing consultant and uploader earnings (REPLACES AdminWalletViewSet)
    
    Endpoints:
    - GET /admin/earnings/ - List all earnings (with filters)
    - GET /admin/earnings/statistics/ - Get earnings statistics
    - GET /admin/earnings/consultant/{id}/ - Get consultant earnings
    - GET /admin/earnings/uploader/{id}/ - Get uploader earnings
    - POST /admin/earnings/{id}/mark-paid/ - Mark earnings as paid out
    """
    permission_classes = [IsAdminUser]
    queryset = ConsultantEarnings.objects.none()  # Override in get_queryset
    
    def get_queryset(self):
        """Get earnings based on type filter"""
        earnings_type = self.request.query_params.get('type', 'consultant')
        
        if earnings_type == 'uploader':
            queryset = UploaderEarnings.objects.all().select_related('uploader', 'material')
        else:
            queryset = ConsultantEarnings.objects.all().select_related('consultant', 'booking')
        
        # Filter by paid status
        paid_status = self.request.query_params.get('paid')
        if paid_status == 'true':
            queryset = queryset.filter(paid_out=True)
        elif paid_status == 'false':
            queryset = queryset.filter(paid_out=False)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            if earnings_type == 'uploader':
                queryset = queryset.filter(uploader_id=user_id)
            else:
                queryset = queryset.filter(consultant_id=user_id)
        
        # Filter by email
        email = self.request.query_params.get('email')
        if email:
            if earnings_type == 'uploader':
                queryset = queryset.filter(uploader__email__icontains=email)
            else:
                queryset = queryset.filter(consultant__email__icontains=email)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """List earnings with basic serialization"""
        queryset = self.get_queryset()
        earnings_type = request.query_params.get('type', 'consultant')
        
        data = []
        for earning in queryset[:100]:  # Limit to 100 for performance
            if earnings_type == 'uploader':
                data.append({
                    'id': earning.id,
                    'uploader': earning.uploader.email,
                    'material': earning.material.title if earning.material else 'N/A',
                    'service_type': earning.service_type,
                    'gross_amount': float(earning.gross_amount),
                    'platform_commission': float(earning.platform_commission),
                    'net_earnings': float(earning.net_earnings),
                    'paid_out': earning.paid_out,
                    'payout_date': earning.payout_date.isoformat() if earning.payout_date else None,
                    'created_at': earning.created_at.isoformat(),
                })
            else:
                data.append({
                    'id': earning.id,
                    'consultant': earning.consultant.email,
                    'booking_id': earning.booking.id if earning.booking else None,
                    'service_type': earning.service_type,
                    'gross_amount': float(earning.gross_amount),
                    'platform_commission': float(earning.platform_commission),
                    'net_earnings': float(earning.net_earnings),
                    'paid_out': earning.paid_out,
                    'payout_date': earning.payout_date.isoformat() if earning.payout_date else None,
                    'created_at': earning.created_at.isoformat(),
                })
        
        return Response({
            'count': queryset.count(),
            'results': data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get earnings statistics"""
        consultant_earnings = ConsultantEarnings.objects.all()
        uploader_earnings = UploaderEarnings.objects.all()
        
        stats = {
            'consultant_earnings': {
                'total_earnings': float(
                    consultant_earnings.aggregate(total=Sum('net_earnings'))['total'] or 0
                ),
                'total_paid_out': float(
                    consultant_earnings.filter(paid_out=True).aggregate(total=Sum('net_earnings'))['total'] or 0
                ),
                'pending_payout': float(
                    consultant_earnings.filter(paid_out=False).aggregate(total=Sum('net_earnings'))['total'] or 0
                ),
                'total_consultants': consultant_earnings.values('consultant').distinct().count(),
            },
            'uploader_earnings': {
                'total_earnings': float(
                    uploader_earnings.aggregate(total=Sum('net_earnings'))['total'] or 0
                ),
                'total_paid_out': float(
                    uploader_earnings.filter(paid_out=True).aggregate(total=Sum('net_earnings'))['total'] or 0
                ),
                'pending_payout': float(
                    uploader_earnings.filter(paid_out=False).aggregate(total=Sum('net_earnings'))['total'] or 0
                ),
                'total_uploaders': uploader_earnings.values('uploader').distinct().count(),
            },
            'platform_commission': {
                'from_consultations': float(
                    consultant_earnings.aggregate(total=Sum('platform_commission'))['total'] or 0
                ),
                'from_materials': float(
                    uploader_earnings.aggregate(total=Sum('platform_commission'))['total'] or 0
                ),
                'total': float(
                    (consultant_earnings.aggregate(total=Sum('platform_commission'))['total'] or 0) +
                    (uploader_earnings.aggregate(total=Sum('platform_commission'))['total'] or 0)
                ),
            }
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark earnings as paid out"""
        earnings_type = request.query_params.get('type', 'consultant')
        
        try:
            if earnings_type == 'uploader':
                earning = UploaderEarnings.objects.get(id=pk)
                user = earning.uploader
            else:
                earning = ConsultantEarnings.objects.get(id=pk)
                user = earning.consultant
        except (ConsultantEarnings.DoesNotExist, UploaderEarnings.DoesNotExist):
            return Response(
                {'error': 'Earning record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if earning.paid_out:
            return Response(
                {'error': 'This earning has already been paid out'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        earning.paid_out = True
        earning.payout_date = timezone.now()
        earning.save()
        
        return Response({
            'message': f'Earnings marked as paid for {user.email}',
            'amount': float(earning.net_earnings),
            'payout_date': earning.payout_date.isoformat()
        })
