#!/usr/bin/env python
"""Quick script to list all registered API endpoints"""

from django.conf import settings
import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
import django
django.setup()

from django.urls import get_resolver
from rest_framework.routers import DefaultRouter

def show_urls(urlpatterns, depth=0, prefix=''):
    """Recursively show all URL patterns"""
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # It's an included URLconf
            new_prefix = prefix + str(pattern.pattern)
            show_urls(pattern.url_patterns, depth + 1, new_prefix)
        else:
            # It's a regular pattern
            path = prefix + str(pattern.pattern)
            # Only show admin and subscription related paths
            if any(keyword in path.lower() for keyword in ['admin', 'subscription', 'transaction', 'earning', 'plan', 'wallet']):
                print(f"  {path}")

print("\n🔍 CHECKING REGISTERED API ENDPOINTS...\n")
print("=" * 70)

# Get the root URL resolver
resolver = get_resolver()

# Show relevant endpoints
print("\n📋 ADMIN & SUBSCRIPTION RELATED ENDPOINTS:")
print("-" * 70)
show_urls(resolver.url_patterns)

print("\n" + "=" * 70)
print("\n✅ Endpoint check complete!\n")
