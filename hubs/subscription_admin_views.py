"""
Admin Views for Subscription Management
Provides complete CRUD operations for managing user subscriptions with time testing capabilities
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q

from subscriptions.models import UserSubscription
from .subscription_serializers import (
    SubscriptionAdminListSerializer,
    SubscriptionAdminDetailSerializer,
    SubscriptionAdminCreateUpdateSerializer,
    SubscriptionTimeExtensionSerializer,
    SubscriptionEndDateSerializer,
    SubscriptionPeriodResetSerializer
)


class SubscriptionAdminViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing User Subscriptions
    
    Provides complete CRUD operations, time management, and bulk operations for subscriptions.
    All endpoints require admin authentication.
    
    Endpoints:
    - GET    /api/v1/admin/hubs/subscriptions/                   - List all subscriptions
    - POST   /api/v1/admin/hubs/subscriptions/                   - Create new subscription
    - GET    /api/v1/admin/hubs/subscriptions/{id}/              - Get subscription details
    - PUT    /api/v1/admin/hubs/subscriptions/{id}/              - Update subscription
    - PATCH  /api/v1/admin/hubs/subscriptions/{id}/              - Partial update subscription
    - DELETE /api/v1/admin/hubs/subscriptions/{id}/              - Delete subscription
    - PATCH  /api/v1/admin/hubs/subscriptions/{id}/extend-time/   - Extend subscription time
    - PATCH  /api/v1/admin/hubs/subscriptions/{id}/set-end-date/ - Set custom end date
    - POST   /api/v1/admin/hubs/subscriptions/{id}/reset-period/  - Reset subscription period
    - POST   /api/v1/admin/hubs/subscriptions/bulk-update/     - Bulk update subscriptions
    - GET    /api/v1/admin/hubs/subscriptions/expiring/         - Get expiring subscriptions
    - GET    /api/v1/admin/hubs/subscriptions/stats/            - Get statistics
    """
    queryset = UserSubscription.objects.all().select_related('user', 'plan')
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'status', 'plan', 'auto_renew']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'plan__name']
    ordering_fields = ['created_at', 'end_date', 'start_date', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionAdminCreateUpdateSerializer
        elif self.action in ['update', 'partial_update']:
            return SubscriptionAdminCreateUpdateSerializer
        elif self.action == 'retrieve':
            return SubscriptionAdminDetailSerializer
        else:
            return SubscriptionAdminListSerializer

    def get_queryset(self):
        """Filter subscriptions based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by plan type
        plan_type = self.request.query_params.get('plan_type')
        if plan_type:
            queryset = queryset.filter(plan__name__icontains=plan_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscription statistics"""
        from django.db.models import Count, Sum, Avg
        from datetime import date
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        
        # Basic counts
        total_subscriptions = queryset.count()
        active_subscriptions = queryset.filter(status='active').count()
        expired_subscriptions = queryset.filter(status='expired').count()
        cancelled_subscriptions = queryset.filter(status='cancelled').count()
        
        # Revenue stats
        total_revenue = queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Plan distribution
        plan_stats = queryset.values('plan__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'expired_subscriptions': expired_subscriptions,
            'cancelled_subscriptions': cancelled_subscriptions,
            'total_revenue': total_revenue,
            'plan_distribution': list(plan_stats),
            'date_from': date_from,
            'date_to': date_to
        }
        
        serializer = SubscriptionAdminDetailSerializer(stats, many=False)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """Get subscriptions expiring soon"""
        days_ahead = int(request.query_params.get('days_ahead', 7))
        cutoff_date = timezone.now() + timedelta(days=days_ahead)
        
        queryset = self.get_queryset().filter(
            status='active',
            end_date__lte=cutoff_date
        ).order_by('end_date')
        
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['patch'])
    def extend_time(self, request, pk=None):
        """Extend subscription time for testing"""
        subscription = self.get_object()
        serializer = SubscriptionTimeExtensionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        extend_days = serializer.validated_data['extend_days']
        extend_hours = serializer.validated_data.get('extend_hours', 0)
        reason = serializer.validated_data.get('reason', 'admin_time_extension')
        notify_user = serializer.validated_data.get('notify_user', False)
        
        # Calculate new end date
        current_end = subscription.end_date or timezone.now()
        new_end_date = current_end + timedelta(days=extend_days, hours=extend_hours)
        
        # Update subscription
        subscription.end_date = new_end_date
        subscription.status = 'active'  # Ensure it's active
        subscription.save()
        
        # Log the change
        from .subscription_models import SubscriptionLog
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='time_extended',
            old_end_date=current_end,
            new_end_date=new_end_date,
            reason=reason,
            admin_user=request.user
        )
        
        # Send notification if requested
        if notify_user:
            # TODO: Implement notification system
            pass
        
        serializer = SubscriptionAdminDetailSerializer(subscription)
        return Response({
            'success': True,
            'message': f'Subscription extended by {extend_days} days and {extend_hours} hours',
            'subscription': serializer.data
        })

    @action(detail=True, methods=['patch'])
    def set_end_date(self, request, pk=None):
        """Set custom end date for testing"""
        subscription = self.get_object()
        serializer = SubscriptionEndDateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_end_date = serializer.validated_data['end_date']
        reason = serializer.validated_data.get('reason', 'admin_custom_end_date')
        notify_user = serializer.validated_data.get('notify_user', False)
        
        old_end_date = subscription.end_date
        
        # Update subscription
        subscription.end_date = new_end_date
        subscription.status = 'active'  # Ensure it's active
        subscription.save()
        
        # Log the change
        from .subscription_models import SubscriptionLog
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='end_date_changed',
            old_end_date=old_end_date,
            new_end_date=new_end_date,
            reason=reason,
            admin_user=request.user
        )
        
        # Send notification if requested
        if notify_user:
            # TODO: Implement notification system
            pass
        
        serializer = SubscriptionAdminDetailSerializer(subscription)
        return Response({
            'success': True,
            'message': f'End date set to {new_end_date}',
            'subscription': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset_period(self, request, pk=None):
        """Reset subscription period for testing"""
        subscription = self.get_object()
        serializer = SubscriptionPeriodResetSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_start_date = serializer.validated_data['new_start_date']
        new_end_date = serializer.validated_data['new_end_date']
        reason = serializer.validated_data.get('reason', 'admin_period_reset')
        reset_renewal_count = serializer.validated_data.get('reset_renewal_count', False)
        notify_user = serializer.validated_data.get('notify_user', False)
        
        old_start_date = subscription.start_date
        old_end_date = subscription.end_date
        
        # Update subscription
        subscription.start_date = new_start_date
        subscription.end_date = new_end_date
        subscription.status = 'active'
        if reset_renewal_count:
            subscription.renewal_count = 0
        subscription.save()
        
        # Log the change
        from .subscription_models import SubscriptionLog
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='period_reset',
            old_start_date=old_start_date,
            new_start_date=new_start_date,
            old_end_date=old_end_date,
            new_end_date=new_end_date,
            reason=reason,
            admin_user=request.user
        )
        
        # Send notification if requested
        if notify_user:
            # TODO: Implement notification system
            pass
        
        serializer = SubscriptionAdminDetailSerializer(subscription)
        return Response({
            'success': True,
            'message': f'Subscription period reset from {old_start_date} to {new_start_date}',
            'subscription': serializer.data
        })

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple subscriptions"""
        subscription_ids = request.data.get('subscription_ids', [])
        extend_days = request.data.get('extend_days', 0)
        reason = request.data.get('reason', 'bulk_admin_update')
        
        if not subscription_ids:
            return Response(
                {'error': 'subscription_ids field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscriptions = UserSubscription.objects.filter(id__in=subscription_ids)
        updated_count = 0
        
        for subscription in subscriptions:
            if extend_days > 0:
                new_end_date = subscription.end_date + timedelta(days=extend_days)
                subscription.end_date = new_end_date
                subscription.status = 'active'
                subscription.save()
                updated_count += 1
                
                # Log the change
                from .subscription_models import SubscriptionLog
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    action='bulk_time_extended',
                    old_end_date=subscription.end_date - timedelta(days=extend_days),
                    new_end_date=new_end_date,
                    reason=reason,
                    admin_user=request.user
                )
        
        return Response({
            'success': True,
            'message': f'Updated {updated_count} subscriptions',
            'updated_count': updated_count,
            'requested_count': len(subscription_ids)
        })

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        """Toggle subscription between active and inactive"""
        subscription = self.get_object()
        
        # Get requested status from request body
        requested_status = request.data.get('status')
        if requested_status not in ['active', 'inactive']:
            return Response({
                'error': 'Status must be either "active" or "inactive"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = subscription.status
        
        # Toggle the status
        if requested_status == 'active':
            subscription.status = 'active'
            action_desc = 'activated'
        else:
            subscription.status = 'inactive'
            action_desc = 'deactivated'
        
        subscription.save()
        
        # Log the change
        from .subscription_models import SubscriptionLog
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='status_changed',
            old_status=old_status,
            new_status=requested_status,
            reason=f'admin_{action_desc}',
            admin_user=request.user
        )
        
        return Response({
            'success': True,
            'message': f'Subscription {action_desc} (was {old_status})',
            'subscription_id': subscription.id,
            'user_email': subscription.user.email,
            'old_status': old_status,
            'new_status': requested_status
        })
