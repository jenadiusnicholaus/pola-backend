# authentication/device_serializers.py
from rest_framework import serializers
from .device_models import UserDevice, UserSession, LoginHistory, SecurityAlert
from django.utils import timezone


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for user devices"""
    is_current_device = serializers.SerializerMethodField()
    days_since_last_seen = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDevice
        fields = [
            'id', 'device_id', 'device_name', 'device_type',
            'os_name', 'os_version', 'browser_name', 'browser_version',
            'app_version', 'device_model', 'device_manufacturer',
            'is_trusted', 'is_active', 'first_seen', 'last_seen',
            'last_ip', 'is_current_device', 'days_since_last_seen'
        ]
        read_only_fields = ['id', 'first_seen', 'last_seen', 'last_ip']
    
    def get_is_current_device(self, obj):
        """Check if this is the current device"""
        request = self.context.get('request')
        if request and hasattr(request, 'device_id'):
            return obj.device_id == request.device_id
        return False
    
    def get_days_since_last_seen(self, obj):
        """Calculate days since last seen"""
        if obj.last_seen:
            delta = timezone.now() - obj.last_seen
            return delta.days
        return None


class RegisterDeviceSerializer(serializers.Serializer):
    """Serializer for registering a new device"""
    device_id = serializers.CharField(max_length=255)
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    device_type = serializers.ChoiceField(choices=UserDevice.DEVICE_TYPE_CHOICES, default='unknown')
    
    # Operating System
    os_name = serializers.ChoiceField(choices=UserDevice.OS_CHOICES, default='unknown')
    os_version = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Browser/App Information
    browser_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    browser_version = serializers.CharField(max_length=100, required=False, allow_blank=True)
    app_version = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # Device Hardware
    device_model = serializers.CharField(max_length=255, required=False, allow_blank=True)
    device_manufacturer = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # FCM Token
    fcm_token = serializers.CharField(required=False, allow_blank=True)
    
    # Location data (from client)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    device_info = UserDeviceSerializer(source='device', read_only=True)
    is_current_session = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    location_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'status', 'ip_address', 'country', 'country_code',
            'city', 'region', 'latitude', 'longitude', 'timezone',
            'isp', 'login_time', 'last_activity', 'logout_time',
            'expires_at', 'device_info', 'is_current_session',
            'is_expired', 'duration', 'location_display'
        ]
        read_only_fields = ['id', 'login_time', 'last_activity', 'logout_time']
    
    def get_is_current_session(self, obj):
        """Check if this is the current session"""
        request = self.context.get('request')
        if request and hasattr(request, 'session'):
            return obj.session_key == request.session.session_key
        return False
    
    def get_is_expired(self, obj):
        """Check if session is expired"""
        return obj.is_expired()
    
    def get_duration(self, obj):
        """Get session duration in seconds"""
        if obj.logout_time:
            end_time = obj.logout_time
        else:
            end_time = timezone.now()
        delta = end_time - obj.login_time
        return int(delta.total_seconds())
    
    def get_location_display(self, obj):
        """Get formatted location string"""
        parts = []
        if obj.city:
            parts.append(obj.city)
        if obj.region:
            parts.append(obj.region)
        if obj.country:
            parts.append(obj.country)
        return ', '.join(parts) if parts else 'Unknown'


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for login history"""
    device_info_display = serializers.SerializerMethodField()
    location_display = serializers.SerializerMethodField()
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'email', 'status', 'failure_reason', 'ip_address',
            'country', 'city', 'device_info', 'is_suspicious',
            'suspicious_reasons', 'timestamp', 'device_info_display',
            'location_display'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_device_info_display(self, obj):
        """Get formatted device info"""
        if obj.device:
            return f"{obj.device.device_model or obj.device.device_type} - {obj.device.os_name}"
        return obj.device_info.get('device_type', 'Unknown')
    
    def get_location_display(self, obj):
        """Get formatted location string"""
        parts = []
        if obj.city:
            parts.append(obj.city)
        if obj.country:
            parts.append(obj.country)
        return ', '.join(parts) if parts else 'Unknown'


class SecurityAlertSerializer(serializers.ModelSerializer):
    """Serializer for security alerts"""
    device_info = UserDeviceSerializer(source='device', read_only=True)
    session_info = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityAlert
        fields = [
            'id', 'alert_type', 'severity', 'title', 'message',
            'details', 'is_read', 'is_resolved', 'resolved_at',
            'notification_sent', 'created_at', 'device_info',
            'session_info', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'notification_sent', 'resolved_at']
    
    def get_session_info(self, obj):
        """Get basic session information"""
        if obj.session:
            return {
                'ip_address': obj.session.ip_address,
                'location': f"{obj.session.city}, {obj.session.country}" if obj.session.city else obj.session.country,
                'login_time': obj.session.login_time
            }
        return None
    
    def get_time_ago(self, obj):
        """Get human-readable time since alert was created"""
        delta = timezone.now() - obj.created_at
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class LocationUpdateSerializer(serializers.Serializer):
    """Serializer for updating location data"""
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    accuracy = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    altitude = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
