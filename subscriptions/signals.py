from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from authentication.models import PolaUser
from .models import UserSubscription, SubscriptionPlan


@receiver(post_save, sender=PolaUser)
def create_user_trial_subscription(sender, instance, created, **kwargs):
    """
    Automatically create free trial subscription for new users.
    Note: Wallet system has been replaced by direct AzamPay payments via PaymentTransaction.
    """
    if created:
        # Create free trial subscription
        try:
            free_trial_plan = SubscriptionPlan.objects.get(plan_type='free_trial')
            
            UserSubscription.objects.create(
                user=instance,
                plan=free_trial_plan,
                status='active',
                end_date=timezone.now() + timedelta(days=1)  # 24 hours
            )
        except SubscriptionPlan.DoesNotExist:
            # Free trial plan not found, skip
            pass
