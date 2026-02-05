"""
User Notification History Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import UserNotification
from .serializers import UserNotificationSerializer


class UserNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user notification history
    
    Endpoints:
    - GET /api/v1/notification/notifications/ - List all notifications
    - GET /api/v1/notification/notifications/{id}/ - Get single notification
    - PATCH /api/v1/notification/notifications/{id}/mark_read/ - Mark as read
    - POST /api/v1/notification/notifications/mark_all_read/ - Mark all as read
    - GET /api/v1/notification/notifications/unread_count/ - Get unread count
    - DELETE /api/v1/notification/notifications/{id}/ - Delete notification
    """
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user only"""
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return UserNotification.objects.none()
        
        queryset = UserNotification.objects.filter(user=self.request.user)
        
        # Filter by unread_only
        unread_only = self.request.query_params.get('unread_only', 'false').lower() == 'true'
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset.select_related('user')
    
    @action(detail=True, methods=['patch'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """
        Mark a specific notification as read
        
        PATCH /api/v1/notification/notifications/{id}/mark_read/
        """
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read',
            'notification': UserNotificationSerializer(notification).data
        })
    
    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user
        
        POST /api/v1/notification/notifications/mark_all_read/
        """
        unread_notifications = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        count = unread_notifications.count()
        unread_notifications.update(is_read=True, read_at=timezone.now())
        
        return Response({
            'success': True,
            'message': f'{count} notifications marked as read',
            'count': count
        })
    
    @action(detail=False, methods=['get'], url_path='unread_count')
    def unread_count(self, request):
        """
        Get count of unread notifications
        
        GET /api/v1/notification/notifications/unread_count/
        """
        count = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({
            'count': count
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a notification
        
        DELETE /api/v1/notification/notifications/{id}/
        """
        notification = self.get_object()
        notification.delete()
        
        return Response({
            'success': True,
            'message': 'Notification deleted'
        }, status=status.HTTP_200_OK)


# Import timezone at the top with other imports
from django.utils import timezone
