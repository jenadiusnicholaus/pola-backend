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
        
        # Extract request information
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Parse user agent
        device_info = parse_user_agent(user_agent)
        
        # Get location from IP
        location_data = get_location_from_ip(ip_address)
        
        # Generate device fingerprint
        device_fingerprint = generate_device_fingerprint(request, device_info)
        
        # Get or create device
        device, created = UserDevice.objects.get_or_create(
            user=user,
            device_id=device_fingerprint,
            defaults={
                'device_name': f"{device_info['os_name']} {device_info['device_type']}",
                'device_type': device_info['device_type'],
                'os_name': device_info['os_name'],
                'os_version': device_info['os_version'],
                'browser_name': device_info['browser_name'],
                'browser_version': device_info['browser_version'],
                'device_model': device_info.get('device_model', ''),
                'device_manufacturer': device_info.get('device_manufacturer', ''),
                'last_ip': ip_address,
            }
        )
        
        # Update device last seen
        device.mark_as_seen(ip_address)
        
        # Create security alert for new device
        if created:
            create_security_alert(
                user=user,
                alert_type='new_device',
                title='New Device Login',
                message=f'A new device ({device.device_name}) logged in from {location_data.get("city", "Unknown")}, {location_data.get("country", "Unknown")}',
                severity='medium',
                device=device,
                session=None,
                details={
                    'device_type': device_info['device_type'],
                    'os': device_info['os_name'],
                    'browser': device_info['browser_name'],
                    'ip_address': ip_address,
                    'location': location_data,
                }
            )
        
        # Get or create session (use device_fingerprint + user as session key)
        session_key = f"{user.id}_{device_fingerprint}"
        
        session, session_created = UserSession.objects.get_or_create(
            user=user,
            device=device,
            session_key=session_key,
            status='active',
            defaults={
                'ip_address': ip_address,
                'country': location_data.get('country', ''),
                'country_code': location_data.get('country_code', ''),
                'city': location_data.get('city', ''),
                'region': location_data.get('region', ''),
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
                'timezone': location_data.get('timezone', ''),
                'isp': location_data.get('isp', ''),
                'user_agent': user_agent,
                'login_time': timezone.now(),
                'expires_at': calculate_session_expiry(remember_me=False),
            }
        )
        
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
        
        return None
    
    def process_response(self, request, response):
        """Process response (no action needed)."""
        return response
