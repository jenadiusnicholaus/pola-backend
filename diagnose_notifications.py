#!/usr/bin/env python
"""
Diagnostic script to check notification system
Run: python manage.py shell < diagnose_notifications.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.models import PolaUser
from authentication.device_models import UserDevice
from notification.models import UserNotification
from hubs.models import CommentMention, HubComment

print("=" * 60)
print("NOTIFICATION SYSTEM DIAGNOSTIC")
print("=" * 60)

# 1. Check recent comments
print("\n📝 RECENT COMMENTS (last 5):")
print("-" * 40)
comments = HubComment.objects.order_by('-created_at')[:5]
if not comments:
    print("  No comments found!")
else:
    for c in comments:
        mentions = c.mentions.count() if hasattr(c, 'mentions') else 0
        print(f"  ID:{c.id} | Author: {c.author.email[:30]} | Mentions: {mentions}")
        print(f"    Text: {c.comment_text[:50]}...")

# 2. Check recent mentions
print("\n🏷️  RECENT MENTIONS (last 5):")
print("-" * 40)
mentions = CommentMention.objects.select_related('mentioned_user', 'mentioned_by', 'comment').order_by('-created_at')[:5]
if not mentions:
    print("  No mentions found! This means:")
    print("  - Flutter app is NOT sending 'mentioned_users' array in comment creation")
    print("  - Or mentions are not being parsed from comment text")
else:
    for m in mentions:
        print(f"  Comment #{m.comment_id}: @{m.mentioned_user.email} by {m.mentioned_by.email}")

# 3. Check notifications
print("\n🔔 RECENT NOTIFICATIONS (last 10):")
print("-" * 40)
notifications = UserNotification.objects.order_by('-created_at')[:10]
if not notifications:
    print("  No notifications in database!")
else:
    for n in notifications:
        status = "✅ SENT" if n.fcm_sent else "❌ NOT SENT"
        print(f"  ID:{n.id} | {n.notification_type} | To: {n.user.email[:25]} | {status}")

# 4. Check FCM tokens
print("\n📱 DEVICES WITH FCM TOKENS:")
print("-" * 40)
all_devices = UserDevice.objects.filter(is_active=True)
devices_with_fcm = all_devices.filter(fcm_token__isnull=False).exclude(fcm_token='')
print(f"  Total active devices: {all_devices.count()}")
print(f"  Devices with FCM token: {devices_with_fcm.count()}")

if devices_with_fcm.count() == 0:
    print("\n  ⚠️  NO DEVICES HAVE FCM TOKENS!")
    print("  This means push notifications CANNOT be delivered.")
    print("  Flutter app must:")
    print("    1. Request notification permission")
    print("    2. Get FCM token from Firebase")
    print("    3. POST token to /api/v1/notifications/fcm-token/")
else:
    print("\n  Users with FCM tokens:")
    for d in devices_with_fcm[:10]:
        print(f"    - {d.user.email} ({d.device_name or 'Unknown device'})")

# 5. Find user "rama"
print("\n🔍 SEARCHING FOR USER 'RAMA':")
print("-" * 40)
rama_users = PolaUser.objects.filter(
    models.Q(username__icontains='rama') | 
    models.Q(first_name__icontains='rama') | 
    models.Q(email__icontains='rama')
)
from django.db import models
rama_users = PolaUser.objects.filter(username__icontains='rama') | PolaUser.objects.filter(first_name__icontains='rama') | PolaUser.objects.filter(email__icontains='rama')

if not rama_users:
    print("  User 'rama' not found!")
else:
    for u in rama_users[:3]:
        print(f"  Found: ID={u.id}, Email={u.email}, Username={u.username}")
        # Check their devices
        user_devices = UserDevice.objects.filter(user=u, is_active=True)
        print(f"    Active devices: {user_devices.count()}")
        for d in user_devices:
            has_fcm = "✅ YES" if d.fcm_token else "❌ NO"
            print(f"      - {d.device_name}: FCM Token: {has_fcm}, Current: {d.is_current_device}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
