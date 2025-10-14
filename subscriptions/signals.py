from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from authentication.models import PolaUser
from .models import Wallet, UserSubscription, SubscriptionPlan


@receiver(post_save, sender=PolaUser)
def create_user_wallet_and_trial(sender, instance, created, **kwargs):
    """
    Automatically create wallet and free trial subscription for new users
    """
    if created:
        # Create wallet
        Wallet.objects.get_or_create(user=instance)
        
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
