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
    Wallet,
    Transaction,
)
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    WalletSerializer,
    TransactionSerializer,
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
                    Transaction.objects.filter(
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


class AdminTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for viewing and managing transactions
    
    Endpoints:
    - GET /admin/transactions/ - List all transactions (with filters)
    - GET /admin/transactions/{id}/ - Get transaction details
    - POST /admin/transactions/{id}/refund/ - Process refund
    - POST /admin/transactions/{id}/complete/ - Mark as completed
    - POST /admin/transactions/{id}/fail/ - Mark as failed
    - POST /admin/transactions/{id}/cancel/ - Cancel transaction
    - GET /admin/transactions/statistics/ - Get transaction statistics
    """
    permission_classes = [IsAdminUser]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all().select_related('wallet', 'wallet__user')
    
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
            queryset = queryset.filter(wallet__user_id=user_id)
        
        # Filter by email
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(wallet__user__email__icontains=email)
        
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
        """Get transaction statistics"""
        all_transactions = Transaction.objects.all()
        completed = all_transactions.filter(status='completed')
        
        # Revenue by transaction type
        revenue_by_type = {}
        for trans_type, _ in Transaction.TRANSACTION_TYPES:
            revenue = completed.filter(
                transaction_type=trans_type
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_by_type[trans_type] = float(revenue)
        
        stats = {
            'total_transactions': all_transactions.count(),
            'completed_transactions': completed.count(),
            'pending_transactions': all_transactions.filter(status='pending').count(),
            'failed_transactions': all_transactions.filter(status='failed').count(),
            'cancelled_transactions': all_transactions.filter(status='cancelled').count(),
            'total_revenue': float(
                completed.filter(
                    transaction_type__in=['subscription', 'consultation_purchase', 
                                         'document_purchase', 'learning_material_purchase']
                ).aggregate(total=Sum('amount'))['total'] or 0
            ),
            'total_deposits': float(
                completed.filter(transaction_type='deposit').aggregate(total=Sum('amount'))['total'] or 0
            ),
            'total_withdrawals': float(
                completed.filter(transaction_type='withdrawal').aggregate(total=Sum('amount'))['total'] or 0
            ),
            'total_refunds': float(
                completed.filter(transaction_type='refund').aggregate(total=Sum('amount'))['total'] or 0
            ),
            'revenue_by_type': revenue_by_type,
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Process a refund for a transaction"""
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
            # Return money to wallet
            wallet = transaction.wallet
            wallet.balance += refund_amount
            wallet.save()
            
            # Create refund transaction
            refund_transaction = Transaction.objects.create(
                wallet=wallet,
                transaction_type='refund',
                amount=refund_amount,
                status='completed',
                description=f'Refund for {transaction.reference}: {reason}',
                payment_reference=transaction.reference
            )
            
            # Update original transaction status if full refund
            if refund_amount == transaction.amount:
                transaction.status = 'cancelled'
                transaction.save()
        
        return Response({
            'message': f'Refund of {refund_amount} TZS processed successfully',
            'reason': reason,
            'original_transaction': TransactionSerializer(transaction).data,
            'refund_transaction': TransactionSerializer(refund_transaction).data,
            'wallet_balance': float(wallet.balance)
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
            'message': f'Transaction {transaction.reference} marked as completed',
            'transaction': TransactionSerializer(transaction).data
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
            'message': f'Transaction {transaction.reference} marked as failed',
            'reason': reason,
            'transaction': TransactionSerializer(transaction).data
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
            'message': f'Transaction {transaction.reference} cancelled',
            'reason': reason,
            'transaction': TransactionSerializer(transaction).data
        })


class AdminWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for viewing and managing wallets
    
    Endpoints:
    - GET /admin/wallets/ - List all wallets
    - GET /admin/wallets/{id}/ - Get wallet details
    - POST /admin/wallets/{id}/adjust/ - Adjust wallet balance
    - POST /admin/wallets/{id}/freeze/ - Freeze wallet
    - POST /admin/wallets/{id}/unfreeze/ - Unfreeze wallet
    - GET /admin/wallets/statistics/ - Get wallet statistics
    """
    permission_classes = [IsAdminUser]
    serializer_class = WalletSerializer
    queryset = Wallet.objects.all().select_related('user')
    
    def get_queryset(self):
        """Filter wallets based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by email
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(user__email__icontains=email)
        
        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Filter by balance
        min_balance = self.request.query_params.get('min_balance')
        if min_balance:
            queryset = queryset.filter(balance__gte=min_balance)
        
        return queryset.order_by('-balance')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get wallet statistics"""
        all_wallets = Wallet.objects.all()
        
        stats = {
            'total_wallets': all_wallets.count(),
            'active_wallets': all_wallets.filter(is_active=True).count(),
            'frozen_wallets': all_wallets.filter(is_active=False).count(),
            'total_balance': float(
                all_wallets.aggregate(total=Sum('balance'))['total'] or 0
            ),
            'total_earnings': float(
                all_wallets.aggregate(total=Sum('total_earnings'))['total'] or 0
            ),
            'total_withdrawn': float(
                all_wallets.aggregate(total=Sum('total_withdrawn'))['total'] or 0
            ),
            'wallets_with_balance': all_wallets.filter(balance__gt=0).count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """Adjust wallet balance (admin adjustment)"""
        wallet = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', 'Admin adjustment')
        
        if not amount:
            return Response(
                {'error': 'amount parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_balance = wallet.balance
        
        with db_transaction.atomic():
            wallet.balance += amount
            if wallet.balance < 0:
                return Response(
                    {'error': 'Adjustment would result in negative balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            wallet.save()
            
            # Create adjustment transaction
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='adjustment',
                amount=abs(amount),
                status='completed',
                description=f'Admin adjustment: {reason}',
            )
        
        return Response({
            'message': f'Wallet balance adjusted for {wallet.user.email}',
            'reason': reason,
            'old_balance': float(old_balance),
            'new_balance': float(wallet.balance),
            'adjustment': float(amount),
            'wallet': WalletSerializer(wallet).data
        })
    
    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        """Freeze a wallet"""
        wallet = self.get_object()
        reason = request.data.get('reason', 'Admin freeze')
        
        wallet.is_active = False
        wallet.save()
        
        return Response({
            'message': f'Wallet frozen for {wallet.user.email}',
            'reason': reason,
            'wallet': WalletSerializer(wallet).data
        })
    
    @action(detail=True, methods=['post'])
    def unfreeze(self, request, pk=None):
        """Unfreeze a wallet"""
        wallet = self.get_object()
        
        wallet.is_active = True
        wallet.save()
        
        return Response({
            'message': f'Wallet unfrozen for {wallet.user.email}',
            'wallet': WalletSerializer(wallet).data
        })
