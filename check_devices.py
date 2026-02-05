#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.device_models import UserDevice
from django.contrib.auth import get_user_model
User = get_user_model()

print("=" * 60)
print("CONSULTANTS AND THEIR DEVICES")
print("=" * 60)

# Find consultants via consultant_profile relationship
from subscriptions.models import ConsultantProfile
profiles = ConsultantProfile.objects.all()
print(f"Found {profiles.count()} consultant profiles")

for p in profiles[:10]:
    c = p.user
    devices = UserDevice.objects.filter(user=c, is_active=True)
    print(f"\n{c.id}: {c.first_name} {c.last_name} ({c.email})")
    if devices.exists():
        for d in devices:
            has_token = f"TOKEN ({len(d.fcm_token)} chars)" if d.fcm_token else "NO TOKEN!"
            print(f"   Device {d.id}: {d.device_name}")
            print(f"      - is_current: {d.is_current_device}")
            print(f"      - fcm_token: {has_token}")
    else:
        print("   NO DEVICES!")
