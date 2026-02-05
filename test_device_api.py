#!/usr/bin/env python
import os, sys
sys.path.insert(0, '/Users/mac/development/python_projects/pola-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
import django
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver

def list_urls(urlpatterns, prefix=''):
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            urls.append(prefix + str(pattern.pattern))
        elif isinstance(pattern, URLResolver):
            urls.extend(list_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
    return urls

resolver = get_resolver()
all_urls = list_urls(resolver.url_patterns)

print("=" * 60)
print("DEVICE & SECURITY API ENDPOINTS")
print("=" * 60)

# Filter device-related URLs
device_urls = [u for u in all_urls if 'device' in u.lower() or 'security' in u.lower()]
for url in sorted(device_urls):
    print(f"  /{url}")

print()
print("=" * 60)
print("NOTIFICATION API ENDPOINTS")
print("=" * 60)

# Filter notification URLs
notif_urls = [u for u in all_urls if 'notification' in u.lower()]
for url in sorted(notif_urls):
    print(f"  /{url}")

# Test if the ViewSet actions exist
print()
print("=" * 60)
print("CHECKING VIEWSET ACTIONS")
print("=" * 60)

from authentication.device_views import UserDeviceViewSet

actions = [m for m in dir(UserDeviceViewSet) if not m.startswith('_')]
custom_actions = ['update_fcm_token', 'update_current_device_token', 'trust', 'untrust', 'deactivate', 'verify_and_register']

print("\nUserDeviceViewSet custom actions:")
for action in custom_actions:
    exists = action in actions
    status = "✅" if exists else "❌"
    print(f"  {status} {action}")
