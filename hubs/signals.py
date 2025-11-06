"""
Django signals for Hub models
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import HubComment


@receiver(pre_save, sender=HubComment)
def update_comment_hub_type(sender, instance, **kwargs):
    """
    Automatically set the comment's hub_type to match its content's hub_type
    This ensures data consistency and prevents comment count issues
    """
    if instance.content and instance.content.hub_type:
        instance.hub_type = instance.content.hub_type