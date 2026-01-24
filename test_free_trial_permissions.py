#!/usr/bin/env python
"""
Test script for Free Trial permissions
Run: python manage.py shell < test_free_trial_permissions.py
"""
import json
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import UserSubscription, SubscriptionPlan
from authentication.models import PolaUser

# Get/create an active trial for testing
user = PolaUser.objects.first()
if user:
    try:
        sub = user.subscription
        # Update to make it active for testing
        sub.end_date = timezone.now() + timedelta(days=1)
        sub.status = 'active'
        sub.save()
    except Exception as e:
        plan = SubscriptionPlan.objects.get(plan_type='free_trial')
        sub = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            end_date=timezone.now() + timedelta(days=1)
        )
    
    print('=== ACTIVE TRIAL USER SUBSCRIPTION ===')
    print(f'User: {user.email}')
    print(f'Plan: {sub.plan.name}')
    print(f'Is Trial: {sub.is_trial()}')
    print(f'Is Active: {sub.is_active()}')
    print()
    print('=== FULL PERMISSIONS (Frontend Format) ===')
    perms = sub.get_permissions()
    print(json.dumps(perms, indent=2, default=str))
    
    print('\n=== FRONTEND EXPECTED FORMAT ===')
    frontend_format = {
        "subscription": {
            "is_trial": sub.is_trial(),
            "is_active": sub.is_active(),
            "permissions": {
                "can_comment_forum": perms.get('can_comment_forum'),
                "can_reply_forum": perms.get('can_reply_forum'),
                "can_download_templates": perms.get('can_download_templates'),
                "can_talk_to_lawyer": perms.get('can_talk_to_lawyer'),
                "can_ask_question": perms.get('can_ask_question'),
                "can_book_consultation": perms.get('can_book_consultation'),
                "can_view_nearby_lawyers": perms.get('can_view_nearby_lawyers'),
                "legal_education_limit": perms.get('legal_education_limit'),
                "legal_education_reads": perms.get('legal_education_reads'),
                "legal_education_remaining": perms.get('legal_education_remaining'),
            }
        }
    }
    print(json.dumps(frontend_format, indent=2, default=str))
else:
    print('No users found')
