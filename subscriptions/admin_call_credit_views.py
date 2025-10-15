"""
Admin Call Credit Bundle Management Views
Handles CRUD operations for call credit bundles and user credits
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import timedelta
from decimal import Decimal

from .models import CallCreditBundle, UserCallCredit, CallSession, PaymentTransaction
from .admin_call_credit_serializers import (
    CallCreditBundleAdminSerializer,
    UserCallCreditAdminSerializer,
    GrantCallCreditSerializer,
    CallCreditStatsSerializer
)
from authentication.models import PolaUser


class CallCreditBundleViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing call credit bundles
    
    Endpoints:
    - GET    /admin/call-credits/bundles/          - List all bundles
    - POST   /admin/call-credits/bundles/          - Create bundle
    - GET    /admin/call-credits/bundles/{id}/     - Get bundle details
    - PUT    /admin/call-credits/bundles/{id}/     - Update bundle
    - DELETE /admin/call-credits/bundles/{id}/     - Delete bundle
    - POST   /admin/call-credits/bundles/{id}/activate/   - Toggle active
    """
    queryset = CallCreditBundle.objects.all()
    serializer_class = CallCreditBundleAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('price')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate or deactivate a bundle"""
        bundle = self.get_object()
        is_active = request.data.get('is_active', True)
        
        bundle.is_active = is_active
        bundle.save()
        
        return Response({
            'success': True,
            'message': f"Bundle {'activated' if is_active else 'deactivated'} successfully",
            'bundle': CallCreditBundleAdminSerializer(bundle).data
        })
    
    @action(detail=True, methods=['get'])
    def purchases(self, request, pk=None):
        """Get all purchases for a bundle"""
        bundle = self.get_object()
        credits = UserCallCredit.objects.filter(bundle=bundle).order_by('-purchase_date')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = UserCallCreditAdminSerializer(credits[start:end], many=True)
        
        return Response({
            'count': credits.count(),
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class UserCallCreditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin API for managing user call credits
    
    Endpoints:
    - GET    /admin/call-credits/users/          - List all user credits
    - GET    /admin/call-credits/users/{id}/     - Get credit details
    - POST   /admin/call-credits/users/grant/    - Grant free credits
    - GET    /admin/call-credits/stats/          - Statistics
    - GET    /admin/call-credits/usage/          - Usage reports
    """
    queryset = UserCallCredit.objects.all()
    serializer_class = UserCallCreditAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by bundle
        bundle_id = self.request.query_params.get('bundle_id')
        if bundle_id:
            queryset = queryset.filter(bundle_id=bundle_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter active credits
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(
                status='active',
                expiry_date__gt=timezone.now(),
                remaining_minutes__gt=0
            )
        
        return queryset.order_by('-purchase_date')
    
    @action(detail=False, methods=['post'])
    def grant(self, request):
        """Grant free call credits to a user"""
        serializer = GrantCallCreditSerializer(data=request.data)
        
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            minutes = serializer.validated_data['minutes']
            validity_days = serializer.validated_data['validity_days']
            reason = serializer.validated_data.get('reason', '')
            
            user = PolaUser.objects.get(id=user_id)
            
            # Create a special "Admin Grant" bundle if doesn't exist
            bundle, created = CallCreditBundle.objects.get_or_create(
                name="Admin Grant (Free)",
                defaults={
                    'minutes': minutes,
                    'price': Decimal('0'),
                    'validity_days': validity_days,
                    'is_active': True
                }
            )
            
            # Create user credit
            credit = UserCallCredit.objects.create(
                user=user,
                bundle=bundle,
                total_minutes=minutes,
                remaining_minutes=minutes,
                expiry_date=timezone.now() + timedelta(days=validity_days),
                status='active'
            )
            
            return Response({
                'success': True,
                'message': f"Granted {minutes} minutes to {user.email}",
                'reason': reason,
                'credit': UserCallCreditAdminSerializer(credit).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get call credit statistics"""
        # Bundles
        total_bundles = CallCreditBundle.objects.count()
        active_bundles = CallCreditBundle.objects.filter(is_active=True).count()
        
        # Purchases
        total_purchases = UserCallCredit.objects.count()
        
        # Revenue
        total_revenue = PaymentTransaction.objects.filter(
            transaction_type='call_credit',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Minutes
        all_credits = UserCallCredit.objects.all()
        total_minutes_sold = sum(c.total_minutes for c in all_credits)
        total_minutes_remaining = sum(c.remaining_minutes for c in all_credits)
        total_minutes_used = total_minutes_sold - total_minutes_remaining
        
        # Active/Expired
        active_credits = UserCallCredit.objects.filter(
            status='active',
            expiry_date__gt=timezone.now()
        ).count()
        expired_credits = UserCallCredit.objects.filter(
            Q(status='expired') | Q(expiry_date__lte=timezone.now())
        ).count()
        
        # Usage rate
        average_usage_rate = (total_minutes_used / total_minutes_sold * 100) if total_minutes_sold > 0 else 0
        
        stats = {
            'total_bundles': total_bundles,
            'active_bundles': active_bundles,
            'total_purchases': total_purchases,
            'total_revenue': total_revenue,
            'total_minutes_sold': total_minutes_sold,
            'total_minutes_used': total_minutes_used,
            'total_minutes_remaining': total_minutes_remaining,
            'active_credits': active_credits,
            'expired_credits': expired_credits,
            'average_usage_rate': round(Decimal(average_usage_rate), 2)
        }
        
        serializer = CallCreditStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def usage(self, request):
        """Get usage reports over time"""
        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly
        
        now = timezone.now()
        
        if period == 'weekly':
            start_date = now - timedelta(weeks=12)
        elif period == 'monthly':
            start_date = now - timedelta(days=365)
        else:  # daily
            start_date = now - timedelta(days=30)
        
        # Get all call sessions in period
        sessions = CallSession.objects.filter(
            start_time__gte=start_date
        ).order_by('start_time')
        
        # Group by period
        usage_data = {}
        for session in sessions:
            if period == 'weekly':
                key = f"{session.start_time.year}-W{session.start_time.isocalendar()[1]}"
            elif period == 'monthly':
                key = session.start_time.strftime('%Y-%m')
            else:  # daily
                key = session.start_time.strftime('%Y-%m-%d')
            
            if key not in usage_data:
                usage_data[key] = {
                    'period': key,
                    'total_calls': 0,
                    'total_minutes': 0,
                    'unique_users': set()
                }
            
            usage_data[key]['total_calls'] += 1
            usage_data[key]['total_minutes'] += session.duration_minutes
            usage_data[key]['unique_users'].add(session.booking.client.id)
        
        # Convert sets to counts
        for key in usage_data:
            usage_data[key]['unique_users'] = len(usage_data[key]['unique_users'])
        
        return Response({
            'period': period,
            'data': list(usage_data.values())
        })
