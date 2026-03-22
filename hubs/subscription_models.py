"""
Subscription Models for Admin Management
Handles subscription logging and tracking for admin operations
"""
from django.db import models
from django.conf import settings


class SubscriptionLog(models.Model):
    """
    Log of all subscription changes made by admin
    Tracks time extensions, period resets, and other modifications
    """
    ACTION_CHOICES = [
        ('time_extended', 'Time Extended'),
        ('end_date_changed', 'End Date Changed'),
        ('period_reset', 'Period Reset'),
        ('bulk_time_extended', 'Bulk Time Extended'),
        ('status_changed', 'Status Changed'),
        ('plan_changed', 'Plan Changed'),
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    ]
    
    subscription = models.ForeignKey(
        'subscriptions.UserSubscription',
        on_delete=models.CASCADE,
        related_name='subscription_logs'
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )
    old_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Previous start date before change"
    )
    new_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="New start date after change"
    )
    old_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Previous end date before change"
    )
    new_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="New end date after change"
    )
    old_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Previous status before change"
    )
    new_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="New status after change"
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for the change"
    )
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_changes'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of admin who made the change"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent of admin who made the change"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'hubs_subscription_log'
        verbose_name = "Subscription Log"
        verbose_name_plural = "Subscription Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['admin_user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.subscription} - {self.get_action_display()} - {self.created_at}"
    
    def get_change_summary(self):
        """Get a human-readable summary of the change"""
        if self.action == 'time_extended':
            if self.old_end_date and self.new_end_date:
                days_extended = (self.new_end_date - self.old_end_date).days
                return f"Extended by {days_extended} days"
        elif self.action == 'end_date_changed':
            if self.old_end_date and self.new_end_date:
                return f"Changed from {self.old_end_date} to {self.new_end_date}"
        elif self.action == 'period_reset':
            return f"Reset period from {self.old_start_date} to {self.new_start_date}"
        
        return self.get_action_display()
