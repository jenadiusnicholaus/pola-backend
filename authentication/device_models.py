# authentication/device_models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class UserDevice(models.Model):
    """
    Store user device information for security tracking
    """
    DEVICE_TYPE_CHOICES = [
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop'),
        ('emulator', 'Emulator'),
        ('unknown', 'Unknown'),
    ]
    
    OS_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('windows', 'Windows'),
        ('macos', 'macOS'),
        ('linux', 'Linux'),
        ('unknown', 'Unknown'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True, help_text="Unique device identifier")
    device_name = models.CharField(max_length=255, blank=True, help_text="User-friendly device name")
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='unknown')
    
    # Operating System
    os_name = models.CharField(max_length=50, choices=OS_CHOICES, default='unknown')
    os_version = models.CharField(max_length=100, blank=True)
    
    # Browser/App Information
    browser_name = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=100, blank=True)
    app_version = models.CharField(max_length=50, blank=True, help_text="Mobile app version")
    
    # Device Hardware
    device_model = models.CharField(max_length=255, blank=True, help_text="e.g., iPhone 13, Samsung Galaxy S21")
    device_manufacturer = models.CharField(max_length=100, blank=True)
    
    # Security
    is_trusted = models.BooleanField(default=False, help_text="User has marked this device as trusted")
    is_active = models.BooleanField(default=True)
    
    # FCM Token for push notifications
    fcm_token = models.TextField(blank=True, help_text="Firebase Cloud Messaging token")
    
    # Tracking
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_devices'
        verbose_name = _('User Device')
        verbose_name_plural = _('User Devices')
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
            models.Index(fields=['last_seen']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name or self.device_model or self.device_id[:8]}"
    
    def mark_as_seen(self, ip_address=None):
        """Update last seen timestamp and IP"""
        self.last_seen = timezone.now()
        if ip_address:
            self.last_ip = ip_address
        self.save(update_fields=['last_seen', 'last_ip', 'updated_at'])


class UserSession(models.Model):
    """
    Track active user sessions with device and location information
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(UserDevice, on_delete=models.SET_NULL, null=True, related_name='sessions')
    
    # Session Information
    session_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # IP and Location
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timezone = models.CharField(max_length=100, blank=True)
    
    # ISP Information
    isp = models.CharField(max_length=255, blank=True, help_text="Internet Service Provider")
    
    # Session Lifecycle
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    # User Agent
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address} ({self.status})"
    
    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at
    
    def terminate(self):
        """Terminate the session"""
        self.status = 'terminated'
        self.logout_time = timezone.now()
        self.save(update_fields=['status', 'logout_time', 'updated_at'])
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity', 'updated_at'])


class LoginHistory(models.Model):
    """
    Track all login attempts (successful and failed)
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]
    
    FAILURE_REASON_CHOICES = [
        ('invalid_credentials', 'Invalid Credentials'),
        ('account_locked', 'Account Locked'),
        ('account_inactive', 'Account Inactive'),
        ('too_many_attempts', 'Too Many Attempts'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='login_history')
    email = models.EmailField(help_text="Email used in login attempt")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    failure_reason = models.CharField(max_length=50, choices=FAILURE_REASON_CHOICES, blank=True)
    
    # Device and Location
    device = models.ForeignKey(UserDevice, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # User Agent
    user_agent = models.TextField(blank=True)
    device_info = models.JSONField(default=dict, help_text="Additional device information")
    
    # Security Flags
    is_suspicious = models.BooleanField(default=False)
    suspicious_reasons = models.JSONField(default=list, help_text="Reasons for flagging as suspicious")
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_history'
        verbose_name = _('Login History')
        verbose_name_plural = _('Login History')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['email', 'status']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_suspicious']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.status} at {self.timestamp}"


class SecurityAlert(models.Model):
    """
    Store security alerts for unusual activity
    """
    ALERT_TYPE_CHOICES = [
        ('new_device', 'New Device Login'),
        ('new_location', 'New Location'),
        ('failed_login', 'Failed Login Attempts'),
        ('password_change', 'Password Changed'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('account_access', 'Account Access from Unknown Device'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    details = models.JSONField(default=dict, help_text="Additional alert details")
    
    # Related Objects
    device = models.ForeignKey(UserDevice, on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Alert Status
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Notification
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'security_alerts'
        verbose_name = _('Security Alert')
        verbose_name_plural = _('Security Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark alert as read"""
        self.is_read = True
        self.save(update_fields=['is_read', 'updated_at'])
    
    def resolve(self):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_at', 'updated_at'])
