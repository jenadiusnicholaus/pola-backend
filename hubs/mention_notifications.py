"""
Notification utilities for user mentions
Sends notifications when users are tagged in comments
"""
from django.utils import timezone
from authentication.models import UserPrivacySettings


def send_mention_notification(mention):
    """
    Send notification when a user is mentioned
    
    Args:
        mention: CommentMention instance
    """
    mentioned_user = mention.mentioned_user
    mentioned_by = mention.mentioned_by
    comment = mention.comment
    
    # Check if user wants to be notified
    if hasattr(mentioned_user, 'privacy_settings'):
        if not mentioned_user.privacy_settings.notify_on_tag:
            return  # User disabled mention notifications
    
    # Check notification preferences
    if not hasattr(mentioned_user, 'notification_preferences'):
        return  # No notification preferences set
    
    prefs = mentioned_user.notification_preferences
    
    # Build notification data
    notification_data = {
        'type': 'mention',
        'title': f'{mentioned_by.get_full_name()} mentioned you',
        'body': _get_comment_preview(comment.comment_text),
        'data': {
            'comment_id': comment.id,
            'mention_id': mention.id,
            'hub_type': comment.hub_type,
            'content_id': comment.content.id,
            'mentioned_by_id': mentioned_by.id,
            'mentioned_by_name': mentioned_by.get_full_name()
        }
    }
    
    # TODO: Integrate with your notification system
    # This is a placeholder - replace with actual notification logic
    
    # Example integrations:
    # 1. Push notification via FCM
    # if prefs.push_enabled and mentioned_user.device_tokens.filter(is_active=True).exists():
    #     send_push_notification(mentioned_user, notification_data)
    
    # 2. Email notification
    # if prefs.email_enabled:
    #     send_email_notification(mentioned_user, notification_data)
    
    # 3. In-app notification
    # create_in_app_notification(mentioned_user, notification_data)
    
    print(f"[NOTIFICATION] {notification_data['title']}: {notification_data['body']}")


def _get_comment_preview(text, max_length=100):
    """Get a preview of comment text"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'


def notify_multiple_mentions(comment):
    """
    Send notifications for all mentions in a comment
    
    Args:
        comment: HubComment instance with mentions
    """
    mentions = comment.mentions.select_related('mentioned_user', 'mentioned_by').all()
    
    for mention in mentions:
        try:
            send_mention_notification(mention)
        except Exception as e:
            # Log error but don't fail the entire operation
            print(f"[ERROR] Failed to send notification for mention {mention.id}: {str(e)}")


# Signal handler to automatically send notifications
# Uncomment and connect this in apps.py if you want automatic notifications
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from hubs.models import CommentMention

@receiver(post_save, sender=CommentMention)
def mention_created(sender, instance, created, **kwargs):
    '''Send notification when a new mention is created'''
    if created:
        send_mention_notification(instance)
"""
