"""
Admin Subscription Management Views
Handles CRUD operations for subscription plans and user subscriptions
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta, datetime
from decimal import Decimal
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import SubscriptionPlan, UserSubscription, PaymentTransaction
from .admin_subscription_serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionAdminSerializer,
    ExtendSubscriptionSerializer,
    GrantSubscriptionSerializer,
    SubscriptionStatsSerializer
)
from authentication.models import PolaUser


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing subscription plans
    
    Endpoints:
    - List all plans
    - Create new plan
    - Update plan
    - Delete plan
    - Activate/deactivate plan
    - View plan subscribers
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminUser]
    
    # Swagger tags
    swagger_tags = ['Admin - Subscription Plans']
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by plan type
        plan_type = self.request.query_params.get('plan_type')
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate or deactivate a plan"""
        plan = self.get_object()
        is_active = request.data.get('is_active', True)
        
        plan.is_active = is_active
        plan.save()
        
        return Response({
            'success': True,
            'message': f"Plan {'activated' if is_active else 'deactivated'} successfully",
            'plan': SubscriptionPlanSerializer(plan).data
        })
    
    @action(detail=True, methods=['get'])
    def subscribers(self, request, pk=None):
        """Get all subscribers for a plan"""
        plan = self.get_object()
        subscriptions = UserSubscription.objects.filter(plan=plan).order_by('-created_at')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = UserSubscriptionAdminSerializer(subscriptions[start:end], many=True)
        
        return Response({
            'count': subscriptions.count(),
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class UserSubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for managing user subscriptions
    
    Endpoints:
    - GET    /admin/subscriptions/users/          - List all user subscriptions
    - GET    /admin/subscriptions/users/{id}/     - Get subscription details
    - PATCH  /admin/subscriptions/users/{id}/extend/    - Extend subscription
    - PATCH  /admin/subscriptions/users/{id}/cancel/    - Cancel subscription
    - POST   /admin/subscriptions/users/grant/          - Grant free subscription
    """
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
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
        
        # Filter active subscriptions
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(
                status='active',
                end_date__gt=timezone.now()
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['patch'])
    def extend(self, request, pk=None):
        """Extend a user's subscription"""
        subscription = self.get_object()
        serializer = ExtendSubscriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            days = serializer.validated_data['days']
            reason = serializer.validated_data.get('reason', '')
            
            subscription.extend_subscription(days)
            
            return Response({
                'success': True,
                'message': f"Subscription extended by {days} days",
                'reason': reason,
                'new_end_date': subscription.end_date,
                'subscription': UserSubscriptionAdminSerializer(subscription).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel a user's subscription"""
        subscription = self.get_object()
        reason = request.data.get('reason', '')
        
        subscription.cancel_subscription()
        
        return Response({
            'success': True,
            'message': "Subscription cancelled successfully",
            'reason': reason,
            'subscription': UserSubscriptionAdminSerializer(subscription).data
        })
    
    @action(detail=False, methods=['post'])
    def grant(self, request):
        """Grant free subscription to a user"""
        serializer = GrantSubscriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            plan_id = serializer.validated_data['plan_id']
            duration_days = serializer.validated_data.get('duration_days')
            reason = serializer.validated_data.get('reason', '')
            
            user = PolaUser.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Check if user already has a subscription
            existing = UserSubscription.objects.filter(user=user).first()
            if existing:
                # Update existing subscription
                existing.plan = plan
                existing.status = 'active'
                existing.start_date = timezone.now()
                existing.end_date = timezone.now() + timedelta(
                    days=duration_days or plan.duration_days
                )
                existing.save()
                subscription = existing
            else:
                # Create new subscription
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    status='active',
                    end_date=timezone.now() + timedelta(
                        days=duration_days or plan.duration_days
                    )
                )
            
            return Response({
                'success': True,
                'message': f"Free subscription granted to {user.email}",
                'reason': reason,
                'subscription': UserSubscriptionAdminSerializer(subscription).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscription statistics"""
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        
        # Total plans
        total_plans = SubscriptionPlan.objects.count()
        active_plans = SubscriptionPlan.objects.filter(is_active=True).count()
        
        # Subscribers
        total_subscribers = UserSubscription.objects.count()
        active_subscribers = UserSubscription.objects.filter(
            status='active',
            end_date__gt=now
        ).count()
        expired_subscribers = UserSubscription.objects.filter(
            Q(status='expired') | Q(end_date__lte=now)
        ).count()
        
        # Trial vs Paid
        trial_users = UserSubscription.objects.filter(
            plan__plan_type='free_trial'
        ).count()
        paid_users = UserSubscription.objects.filter(
            plan__plan_type='monthly'
        ).count()
        
        # Revenue
        total_revenue = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_revenue = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            status='completed',
            created_at__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Churn rate (cancelled this month / total active last month)
        cancelled_this_month = UserSubscription.objects.filter(
            status='cancelled',
            updated_at__gte=start_of_month
        ).count()
        active_last_month = UserSubscription.objects.filter(
            status='active',
            created_at__lt=start_of_month
        ).count()
        churn_rate = (cancelled_this_month / active_last_month * 100) if active_last_month > 0 else 0
        
        # Growth rate
        new_this_month = UserSubscription.objects.filter(
            created_at__gte=start_of_month
        ).count()
        total_last_month = UserSubscription.objects.filter(
            created_at__lt=start_of_month
        ).count()
        growth_rate = (new_this_month / total_last_month * 100) if total_last_month > 0 else 0
        
        stats = {
            'total_plans': total_plans,
            'active_plans': active_plans,
            'total_subscribers': total_subscribers,
            'active_subscribers': active_subscribers,
            'expired_subscribers': expired_subscribers,
            'trial_users': trial_users,
            'paid_users': paid_users,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'churn_rate': round(Decimal(churn_rate), 2),
            'growth_rate': round(Decimal(growth_rate), 2)
        }
        
        serializer = SubscriptionStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue breakdown over time"""
        period = request.query_params.get('period', 'monthly')  # daily, weekly, monthly, yearly
        
        now = timezone.now()
        
        if period == 'daily':
            start_date = now - timedelta(days=30)
            group_by = 'day'
        elif period == 'weekly':
            start_date = now - timedelta(weeks=12)
            group_by = 'week'
        elif period == 'yearly':
            start_date = now - timedelta(days=365*2)
            group_by = 'year'
        else:  # monthly
            start_date = now - timedelta(days=365)
            group_by = 'month'
        
        transactions = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            status='completed',
            created_at__gte=start_date
        ).order_by('created_at')
        
        # Group by period
        revenue_data = {}
        for transaction in transactions:
            if group_by == 'day':
                key = transaction.created_at.strftime('%Y-%m-%d')
            elif group_by == 'week':
                key = f"{transaction.created_at.year}-W{transaction.created_at.isocalendar()[1]}"
            elif group_by == 'year':
                key = str(transaction.created_at.year)
            else:  # month
                key = transaction.created_at.strftime('%Y-%m')
            
            if key not in revenue_data:
                revenue_data[key] = {'period': key, 'revenue': Decimal('0'), 'count': 0}
            
            revenue_data[key]['revenue'] += transaction.amount
            revenue_data[key]['count'] += 1
        
        return Response({
            'period': period,
            'data': list(revenue_data.values())
        })


class AdminPaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for viewing all payment transactions
    
    Endpoints:
    - GET /api/v1/admin/subscriptions/transactions/ - List all transactions
    - GET /api/v1/admin/subscriptions/transactions/{id}/ - Get transaction details
    
    Query Parameters:
    - user_id: Filter by user ID
    - status: Filter by transaction status (pending, completed, failed, refunded, cancelled)
    - transaction_type: Filter by type (subscription, consultation, learning_material, document, call_credit)
    - payment_method: Filter by payment method (mobile_money, bank_transfer, card)
    - date_from: Filter transactions from this date (YYYY-MM-DD)
    - date_to: Filter transactions to this date (YYYY-MM-DD)
    - search: Search by payment reference, gateway reference, or user email
    """
    permission_classes = [IsAdminUser]
    
    # Swagger tags
    swagger_tags = ['Admin - Payment Transactions']
    
    def get_queryset(self):
        """
        Get all payment transactions with filtering - excludes staff/superuser transactions
        """
        queryset = PaymentTransaction.objects.select_related(
            'user',
            'related_subscription__plan',
            'related_booking__consultant',
            'related_booking__client',
        ).exclude(
            user__is_staff=True
        ).exclude(
            user__is_superuser=True
        ).order_by('-created_at')
        
        # Filter by user_id
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by transaction_type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by payment_method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=from_date)
            except ValueError:
                pass
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                # Add 1 day to include the entire end date
                to_date = to_date + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=to_date)
            except ValueError:
                pass
        
        # Search by payment reference, gateway reference, or user email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(payment_reference__icontains=search) |
                Q(gateway_reference__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Use the public PaymentTransactionSerializer"""
        from .public_serializers import PaymentTransactionSerializer
        return PaymentTransactionSerializer
    
    @swagger_auto_schema(
        operation_description="List all payment transactions with filtering options",
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description="Filter by user ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (pending, completed, failed, refunded, cancelled)", type=openapi.TYPE_STRING),
            openapi.Parameter('transaction_type', openapi.IN_QUERY, description="Filter by type (subscription, consultation, learning_material, document, call_credit)", type=openapi.TYPE_STRING),
            openapi.Parameter('payment_method', openapi.IN_QUERY, description="Filter by payment method (mobile_money, bank_transfer, card)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Filter from date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Filter to date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by payment reference, gateway reference, or user email", type=openapi.TYPE_STRING),
        ],
        tags=['Admin - Payment Transactions']
    )
    def list(self, request, *args, **kwargs):
        """List all payment transactions with filtering"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get detailed information about a specific payment transaction",
        tags=['Admin - Payment Transactions']
    )
    def retrieve(self, request, *args, **kwargs):
        """Get transaction details"""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='get',
        operation_description="Get payment transaction statistics",
        tags=['Admin - Payment Transactions']
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get transaction statistics
        GET /api/v1/admin/subscriptions/transactions/statistics/
        """
        queryset = self.get_queryset()
        
        # Overall stats
        total_transactions = queryset.count()
        total_revenue = queryset.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # By status
        status_stats = {}
        for status_choice in ['pending', 'completed', 'failed', 'refunded', 'cancelled']:
            count = queryset.filter(status=status_choice).count()
            amount = queryset.filter(status=status_choice).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            status_stats[status_choice] = {
                'count': count,
                'total_amount': float(amount)
            }
        
        # By transaction type
        type_stats = {}
        for type_choice in ['subscription', 'consultation', 'learning_material', 'document', 'call_credit']:
            count = queryset.filter(transaction_type=type_choice).count()
            amount = queryset.filter(transaction_type=type_choice, status='completed').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            type_stats[type_choice] = {
                'count': count,
                'total_amount': float(amount)
            }
        
        # By payment method
        method_stats = {}
        for method_choice in ['mobile_money', 'bank_transfer', 'card']:
            count = queryset.filter(payment_method=method_choice).count()
            amount = queryset.filter(payment_method=method_choice, status='completed').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            method_stats[method_choice] = {
                'count': count,
                'total_amount': float(amount)
            }
        
        return Response({
            'total_transactions': total_transactions,
            'total_revenue': float(total_revenue),
            'by_status': status_stats,
            'by_transaction_type': type_stats,
            'by_payment_method': method_stats
        })
