"""
Admin User Management Views
Handles user listing, details, activation/deactivation, and statistics
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from authentication.models import PolaUser, UserRole
from .admin_user_serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    UserStatsSerializer
)


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing users
    
    Endpoints:
    - GET    /admin/users/                    - List all users
    - GET    /admin/users/{id}/               - Get user details
    - PATCH  /admin/users/{id}/               - Update user
    - DELETE /admin/users/{id}/               - Delete user
    - POST   /admin/users/{id}/activate/      - Activate user
    - POST   /admin/users/{id}/deactivate/    - Deactivate user
    - POST   /admin/users/{id}/make-staff/    - Make user staff
    - POST   /admin/users/{id}/remove-staff/  - Remove staff status
    - GET    /admin/users/stats/              - User statistics
    """
    queryset = PolaUser.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by staff status
        is_staff = self.request.query_params.get('is_staff')
        if is_staff is not None:
            queryset = queryset.filter(is_staff=is_staff.lower() == 'true')
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(user_role__role_name=role)
        
        # Search by email or name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filter by date joined
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(date_joined__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(date_joined__lte=end_date)
        
        return queryset.select_related('user_role', 'contact', 'address').order_by('-date_joined')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account"""
        user = self.get_object()
        user.is_active = True
        user.save()
        
        return Response({
            'success': True,
            'message': f'User {user.email} activated successfully',
            'user': UserDetailSerializer(user).data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account"""
        user = self.get_object()
        
        # Prevent deactivating yourself
        if user == request.user:
            return Response({
                'success': False,
                'message': 'You cannot deactivate your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = False
        user.save()
        
        return Response({
            'success': True,
            'message': f'User {user.email} deactivated successfully',
            'user': UserDetailSerializer(user).data
        })
    
    @action(detail=True, methods=['post'])
    def make_staff(self, request, pk=None):
        """Give user staff privileges"""
        user = self.get_object()
        user.is_staff = True
        user.save()
        
        return Response({
            'success': True,
            'message': f'User {user.email} is now staff',
            'user': UserDetailSerializer(user).data
        })
    
    @action(detail=True, methods=['post'])
    def remove_staff(self, request, pk=None):
        """Remove staff privileges from user"""
        user = self.get_object()
        
        # Prevent removing your own staff status
        if user == request.user:
            return Response({
                'success': False,
                'message': 'You cannot remove your own staff status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_staff = False
        user.save()
        
        return Response({
            'success': True,
            'message': f'Staff privileges removed from {user.email}',
            'user': UserDetailSerializer(user).data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        all_users = PolaUser.objects.all()
        
        # Basic counts
        total_users = all_users.count()
        active_users = all_users.filter(is_active=True).count()
        inactive_users = all_users.filter(is_active=False).count()
        staff_users = all_users.filter(is_staff=True).count()
        
        # Verified users (with verified phone)
        verified_users = all_users.filter(contact__phone_is_verified=True).count()
        
        # Users with subscriptions
        from .models import UserSubscription
        users_with_subscriptions = UserSubscription.objects.values('user').distinct().count()
        
        # New users this month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = all_users.filter(date_joined__gte=month_start).count()
        
        # New users this week
        week_start = now - timedelta(days=7)
        new_users_this_week = all_users.filter(date_joined__gte=week_start).count()
        
        # Users by role
        users_by_role = {}
        roles = UserRole.objects.all()
        for role in roles:
            count = all_users.filter(user_role=role).count()
            users_by_role[role.role_name] = count
        
        # Users without role
        users_by_role['no_role'] = all_users.filter(user_role__isnull=True).count()
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'staff_users': staff_users,
            'verified_users': verified_users,
            'users_with_subscriptions': users_with_subscriptions,
            'new_users_this_month': new_users_this_month,
            'new_users_this_week': new_users_this_week,
            'users_by_role': users_by_role,
        }
        
        serializer = UserStatsSerializer(stats)
        return Response(serializer.data)
