#!/usr/bin/env python
import os
import sys
sys.path.insert(0, '/Users/mac/development/python_projects/pola-backend')
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from hubs.models import HubComment, CommentMention
from authentication.models import PolaUser
from authentication.device_models import UserDevice
from notification.models import UserNotification

# Find Michael (both spellings)
print("=== Users named Michael/Micheal ===")
michaels = list(PolaUser.objects.filter(first_name__icontains='michael')[:5])
michaels += list(PolaUser.objects.filter(email__icontains='micheal')[:5])
for u in michaels:
    devs = UserDevice.objects.filter(user=u, is_active=True)
    print(f"  ID={u.id}, {u.first_name} {u.last_name}, {u.email}")
    print(f"    Active devices: {devs.count()}")
    for d in devs:
        has_token = "Yes" if d.fcm_token else "No"
        print(f"      Device: {d.device_name}, Token: {has_token}")

# Recent comments with michael (both spellings)
print("\n=== Recent comments containing 'michael' or 'micheal' ===")
from django.db.models import Q
comments = HubComment.objects.filter(Q(comment_text__icontains='michael') | Q(comment_text__icontains='micheal')).order_by('-created_at')[:5]
for c in comments:
    print(f"  Comment ID: {c.id}")
    print(f"  Author: {c.author.email}")
    print(f"  Text: {c.comment_text[:100]}")
    print(f"  Mentions in DB: {c.mentions.count()}")
    for m in c.mentions.all():
        print(f"    -> Mentioned: {m.mentioned_user.email}")
    print()

# Total mentions
print(f"=== Total CommentMention records in DB: {CommentMention.objects.count()} ===")

# Michael's devices
if michaels:
    michael = michaels[0]
    devices = UserDevice.objects.filter(user=michael, is_active=True)
    print(f"\n=== {michael.email} has {devices.count()} active devices ===")
    for d in devices:
        has_token = "Yes" if d.fcm_token else "No"
        print(f"  Device: {d.device_name or d.device_id[:20]}, Has FCM Token: {has_token}")

# Recent notifications
print("\n=== Recent notifications ===")
for n in UserNotification.objects.order_by('-created_at')[:5]:
    print(f"  {n.id}: {n.user.email} - {n.notification_type} - FCM sent: {n.fcm_sent}")
