from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .device_models import UserDevice, UserSession, LoginHistory
from .device_utils import (
    get_client_ip,
    parse_user_agent,
    get_location_from_ip,
    generate_device_fingerprint,
    detect_suspicious_activity,
    create_security_alert,
    calculate_session_expiry,
)
from notification.models import UserOnlineStatus


class SecurityTrackingMiddleware(MiddlewareMixin):
    """
    Automatically track user devices, sessions, and activity.
    
    This middleware:
    - Creates/updates UserDevice on authenticated requests
    - Creates/updates UserSession for authenticated users
    - Updates last_activity timestamp on sessions
    - Tracks device location changes
    """
    
    def process_request(self, request):
        """Process incoming request to track security information."""
        
        # Skip tracking for non-authenticated requests
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            # Try to authenticate using JWT
            try:
                jwt_auth = JWTAuthentication()
                auth_result = jwt_auth.authenticate(request)
                if auth_result:
                    request.user, request.auth = auth_result
                else:
                    return None
            except (AuthenticationFailed, Exception):
                return None
        
        # Get user
        user = request.user
        if not user.is_authenticated:
            return None
        
        # Update user online status FIRST (regardless of device registration)
        try:
            online_status, created = UserOnlineStatus.objects.get_or_create(
                user=user
            )
            
            # Update last heartbeat
            online_status.last_heartbeat = timezone.now()
            
            # Only mark as online if not currently busy (in a call)
            if online_status.status != 'busy':
                online_status.is_online = True
                online_status.status = 'available'
            
            online_status.save(update_fields=['last_heartbeat', 'is_online', 'status'])
            
        except Exception as e:
            # Don't break the request if online status tracking fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating online status for user {user.id}: {e}")
        
        # Wrap everything in try-except to prevent errors from blocking requests
        try:
            # Extract request information
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Parse user agent
            device_info = parse_user_agent(user_agent)
            
            # Get location from IP
            location_data = get_location_from_ip(ip_address)
            
            # Generate device fingerprint
            device_fingerprint = generate_device_fingerprint(request, device_info)
            
            # Check if device exists (DON'T create, only use registered devices)
            device = UserDevice.objects.filter(
                user=user,
                device_id=device_fingerprint,
                is_active=True
            ).first()
            
            # If device not registered, skip session tracking
            # Device must be registered via /api/v1/security/devices/ first
            if not device:
                return None
            
            # Update device last seen
            device.mark_as_seen(ip_address)
            
            # Get or create session (use device_fingerprint + user as session key)
            session_key = f"{user.id}_{device_fingerprint}"
            
            # Try to get existing session
            session = UserSession.objects.filter(
                session_key=session_key
            ).first()
            
            session_created = False
            
            if session:
                # Reactivate if expired or terminated
                if session.status != 'active':
                    session.status = 'active'
                    session.expires_at = calculate_session_expiry(remember_me=False)
                    session.save()
            else:
                # Create new session
                session = UserSession.objects.create(
                    user=user,
                    device=device,
                    session_key=session_key,
                    status='active',
                    ip_address=ip_address,
                    country=location_data.get('country', ''),
                    country_code=location_data.get('country_code', ''),
                    city=location_data.get('city', ''),
                    region=location_data.get('region', ''),
                    latitude=location_data.get('latitude'),
                    longitude=location_data.get('longitude'),
                    timezone=location_data.get('timezone', ''),
                    isp=location_data.get('isp', ''),
                    user_agent=user_agent,
                    login_time=timezone.now(),
                    expires_at=calculate_session_expiry(remember_me=False),
                )
                session_created = True
            
            # Update session activity
            if not session_created:
                session.update_activity()
                
                # Check if location changed significantly
                if location_data.get('country') and session.country != location_data.get('country'):
                    create_security_alert(
                        user=user,
                        alert_type='new_location',
                        title='New Location Detected',
                        message=f'Your account was accessed from {location_data.get("city", "Unknown")}, {location_data.get("country", "Unknown")}',
                        severity='medium',
                        device=device,
                        session=session,
                        details={
                            'previous_country': session.country,
                            'new_country': location_data.get('country'),
                            'ip_address': ip_address,
                        }
                    )
                    
                    # Update session location
                    session.ip_address = ip_address
                    session.country = location_data.get('country', '')
                    session.country_code = location_data.get('country_code', '')
                    session.city = location_data.get('city', '')
                    session.region = location_data.get('region', '')
                    session.latitude = location_data.get('latitude')
                    session.longitude = location_data.get('longitude')
                    session.save()
            
            # Attach session and device to request for use in views
            request.user_session = session
            request.user_device = device
            
        except Exception as e:
            # Log the error but don't block the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Security tracking middleware error: {str(e)}")
            # Don't attach anything to request if there was an error
            pass
        
        return None
    
    def process_response(self, request, response):
        """Process response (no action needed)."""
        return response
