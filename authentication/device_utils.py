# authentication/device_utils.py
"""
Utility functions for device and location tracking
"""
import requests
from django.conf import settings
from user_agents import parse
from datetime import timedelta
from django.utils import timezone
import hashlib


def get_client_ip(request):
    """
    Extract client IP address from request
    Handles proxy headers correctly
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device information
    Returns dict with device details
    """
    ua = parse(user_agent_string)
    
    # Determine device type
    if ua.is_mobile:
        device_type = 'mobile'
    elif ua.is_tablet:
        device_type = 'tablet'
    elif ua.is_pc:
        device_type = 'desktop'
    else:
        device_type = 'unknown'
    
    # Determine OS
    os_name = 'unknown'
    if ua.os.family:
        os_lower = ua.os.family.lower()
        if 'android' in os_lower:
            os_name = 'android'
        elif 'ios' in os_lower or 'iphone' in os_lower:
            os_name = 'ios'
        elif 'windows' in os_lower:
            os_name = 'windows'
        elif 'mac' in os_lower or 'macos' in os_lower:
            os_name = 'macos'
        elif 'linux' in os_lower:
            os_name = 'linux'
    
    return {
        'device_type': device_type,
        'os_name': os_name,
        'os_version': ua.os.version_string or '',
        'browser_name': ua.browser.family or '',
        'browser_version': ua.browser.version_string or '',
        'device_model': ua.device.model or '',
        'device_manufacturer': ua.device.brand or '',
    }


def get_location_from_ip(ip_address):
    """
    Get location information from IP address using ipapi.co
    Free tier: 1000 requests per day
    """
    if not ip_address or ip_address in ['127.0.0.1', 'localhost']:
        return {
            'country': 'Local',
            'country_code': 'LOCAL',
            'city': 'Local',
            'region': 'Local',
            'latitude': None,
            'longitude': None,
            'timezone': 'UTC',
            'isp': 'Local'
        }
    
    try:
        # Using ipapi.co (free tier)
        response = requests.get(
            f'https://ipapi.co/{ip_address}/json/',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country_name', ''),
                'country_code': data.get('country_code', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'timezone': data.get('timezone', ''),
                'isp': data.get('org', ''),
            }
    except Exception as e:
        print(f"Error getting location from IP: {e}")
    
    return {
        'country': '',
        'country_code': '',
        'city': '',
        'region': '',
        'latitude': None,
        'longitude': None,
        'timezone': '',
        'isp': '',
    }


def generate_device_fingerprint(request, device_data):
    """
    Generate a unique device fingerprint based on device characteristics
    This is a simple implementation - can be enhanced with more sophisticated methods
    """
    components = [
        device_data.get('device_id', ''),
        device_data.get('os_name', ''),
        device_data.get('os_version', ''),
        device_data.get('device_model', ''),
        device_data.get('device_manufacturer', ''),
        request.META.get('HTTP_USER_AGENT', ''),
    ]
    
    fingerprint_string = '|'.join(str(c) for c in components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()


def detect_suspicious_activity(user, ip_address, location_data):
    """
    Detect suspicious login activity
    Returns tuple: (is_suspicious, reasons)
    """
    from .device_models import LoginHistory, UserSession
    
    reasons = []
    is_suspicious = False
    
    # Check for rapid location changes (impossible travel)
    recent_sessions = UserSession.objects.filter(
        user=user,
        login_time__gte=timezone.now() - timedelta(hours=2)
    ).exclude(
        country=''
    ).order_by('-login_time')[:1]
    
    if recent_sessions.exists():
        last_session = recent_sessions.first()
        if (last_session.country and location_data.get('country') and 
            last_session.country != location_data.get('country')):
            # Different country within 2 hours - suspicious
            reasons.append('impossible_travel')
            is_suspicious = True
    
    # Check for multiple failed login attempts from same IP
    failed_attempts = LoginHistory.objects.filter(
        email=user.email,
        ip_address=ip_address,
        status='failed',
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if failed_attempts >= 3:
        reasons.append('multiple_failed_attempts')
        is_suspicious = True
    
    # Check for new/unusual location
    previous_logins_from_country = UserSession.objects.filter(
        user=user,
        country=location_data.get('country', '')
    ).exists()
    
    if location_data.get('country') and not previous_logins_from_country:
        reasons.append('new_location')
        # Don't mark as suspicious for new location alone, just flag it
    
    return is_suspicious, reasons


def create_security_alert(user, alert_type, title, message, severity='medium', 
                         device=None, session=None, details=None):
    """
    Create a security alert for the user
    """
    from .device_models import SecurityAlert
    
    alert = SecurityAlert.objects.create(
        user=user,
        alert_type=alert_type,
        title=title,
        message=message,
        severity=severity,
        device=device,
        session=session,
        details=details or {}
    )
    
    # TODO: Send notification (email, push, SMS)
    # For now, just mark as notification sent
    alert.notification_sent = True
    alert.notification_sent_at = timezone.now()
    alert.save()
    
    return alert


def calculate_session_expiry(remember_me=False):
    """
    Calculate session expiry time
    """
    if remember_me:
        # 30 days for remember me
        return timezone.now() + timedelta(days=30)
    else:
        # 7 days for regular sessions
        return timezone.now() + timedelta(days=7)
