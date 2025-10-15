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
    - GET    /admin/subscriptions/plans/          - List all plans
    - POST   /admin/subscriptions/plans/          - Create new plan
    - GET    /admin/subscriptions/plans/{id}/     - Get plan details
    - PUT    /admin/subscriptions/plans/{id}/     - Update plan
    - PATCH  /admin/subscriptions/plans/{id}/     - Partial update
    - DELETE /admin/subscriptions/plans/{id}/     - Delete plan
    - POST   /admin/subscriptions/plans/{id}/activate/   - Activate/deactivate plan
    """
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminUser]
    
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
