from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

User = get_user_model()
from django.db import models
from django.utils import timezone
import datetime
import pytz


class FcmTokenModel(models.Model):
    STALE_TIME = (
        ('1m', '1 Minute'),
        ('5m', '5 Minutes'),
        ('10m', '10 Minutes'),
        ('1', '1 Day'),
        ('3', '3 Days'),
        ('7', '1 Week'),
        ('14', '2 Weeks'),
        ('30', '1 Month'),
        ('90', '3 Months'),
        ('180', '6 Months'),
        ('365', '1 Year'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fcm_tokens', null=True, blank=True)
    fcm_token = models.CharField(max_length=1000)
    time_stamp = models.DateTimeField(auto_now_add=True)
    is_stale = models.BooleanField(default=False)
    stale_time = models.CharField(max_length=255, choices=STALE_TIME, default='1')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        verbose_name = 'FCM Token'
        verbose_name_plural = 'FCM Tokens'

    def __str__(self):
        return self.fcm_token
    
    def save(self, *args, **kwargs):
        self.is_stale = self.isStale()
        super(FcmTokenModel, self).save(*args, **kwargs)



    def isStale(self):
        try:
            # Ensure time_stamp is not None
            if self.time_stamp is None:
                print("Error: time_stamp is None")
                return False

            # Define the local timezone
            local_tz = pytz.timezone('Africa/Dar_es_Salaam')

            if self.stale_time.endswith('m'):
                minutes = int(self.stale_time[:-1])
                expiration_time = self.time_stamp + datetime.timedelta(minutes=minutes)
            else:
                days = int(self.stale_time)
                expiration_time = self.time_stamp + datetime.timedelta(days=days)
            
            # Ensure both timestamps are timezone-aware and converted to local timezone
            if timezone.is_naive(expiration_time):
                expiration_time = timezone.make_aware(expiration_time, timezone.get_current_timezone())
            expiration_time = expiration_time.astimezone(local_tz)
            
            current_time = timezone.now().astimezone(local_tz)

            print(f"Expiration Time: {expiration_time}")
            print(f"Current Time: {current_time}")

            return expiration_time < current_time
        except Exception as e:
            print(f"Error in isStale: {e}")
            return False

            
class FcmNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_notifications', null=True, blank=True)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_notifications_to_user', null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class UserOnlineStatus(models.Model):
    """
    Track user online status and availability for incoming calls
    Updated via heartbeat (every 30 seconds)
    """
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    is_online = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    last_heartbeat = models.DateTimeField(null=True, blank=True, help_text="Last heartbeat timestamp")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Online Status'
        verbose_name_plural = 'User Online Statuses'
    
    def __str__(self):
        return f"{self.user.email} - {self.status}"
    
    def mark_online(self):
        """Mark user as online"""
        self.is_online = True
        self.status = 'available'
        self.last_heartbeat = timezone.now()
        self.save()
    
    def mark_offline(self):
        """Mark user as offline"""
        self.is_online = False
        self.status = 'offline'
        self.save()
    
    def mark_busy(self):
        """Mark user as busy (on another call)"""
        self.status = 'busy'
        self.save()
    
    def is_available_for_call(self):
        """Check if user is available for incoming calls"""
        if not self.is_online or self.status != 'available':
            return False
        
        # Check if last heartbeat was within 1 minute
        if self.last_heartbeat:
            time_since_heartbeat = timezone.now() - self.last_heartbeat
            if time_since_heartbeat.total_seconds() > 60:
                self.mark_offline()
                return False
        
        return True


class UserNotification(models.Model):
    """
    Store notification history for users
    Allows users to view past notifications even if FCM was not delivered
    """
    NOTIFICATION_TYPES = [
        ('mention', 'Mention'),
        ('reply', 'Reply'),
        ('consultation_request', 'Consultation Request'),
        ('consultation_status', 'Consultation Status'),
        ('payment_received', 'Payment Received'),
        ('document_ready', 'Document Ready'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(
        default=dict,
        help_text="Additional data payload for navigation"
    )
    
    # Status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    fcm_sent = models.BooleanField(
        default=False,
        help_text="Whether FCM push was successfully sent"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Notification'
        verbose_name_plural = 'User Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])




    
    