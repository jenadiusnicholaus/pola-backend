"""
Middleware to automatically track user online status based on request activity
"""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import UserOnlineStatus
import logging

logger = logging.getLogger(__name__)


class UserOnlineStatusMiddleware(MiddlewareMixin):
    """
    Automatically update user online status on every authenticated request
    This ensures consultant availability is tracked without requiring explicit heartbeat calls
    """
    
    def process_request(self, request):
        """Update user's last_heartbeat on every request"""
        if request.user and request.user.is_authenticated:
            try:
                # Get or create online status
                online_status, created = UserOnlineStatus.objects.get_or_create(
                    user=request.user
                )
                
                # Update last heartbeat
                online_status.last_heartbeat = timezone.now()
                
                # Only mark as online if not currently busy (in a call)
                if online_status.status != 'busy':
                    online_status.is_online = True
                    online_status.status = 'available'
                
                online_status.save(update_fields=['last_heartbeat', 'is_online', 'status'])
                
            except Exception as e:
                # Don't break the request if tracking fails
                logger.error(f"Error updating online status for user {request.user.id}: {e}")
        
        return None
