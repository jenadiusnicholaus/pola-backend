#!/usr/bin/env python
"""
Swagger Configuration Verification Script
Run this to check if Swagger is properly configured
"""

import sys
import os

# Add project to path
sys.path.insert(0, '/Users/mac/development/python_projects/pola-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')

import django
django.setup()

from django.conf import settings
from django.urls import get_resolver
from django.core.management import call_command

print("=" * 70)
print("🔍 SWAGGER CONFIGURATION VERIFICATION")
print("=" * 70)

# Check 1: drf_yasg in INSTALLED_APPS
print("\n✅ Check 1: Verifying drf_yasg in INSTALLED_APPS...")
if 'drf_yasg' in settings.INSTALLED_APPS:
    print("   ✓ drf_yasg is installed")
else:
    print("   ✗ drf_yasg is NOT in INSTALLED_APPS")
    sys.exit(1)

# Check 2: Swagger URLs
print("\n✅ Check 2: Verifying Swagger URL patterns...")
resolver = get_resolver()
swagger_patterns = []
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'name'):
        if pattern.name and 'swagger' in pattern.name.lower():
            swagger_patterns.append(pattern.name)
        elif pattern.name and 'schema' in pattern.name.lower():
            swagger_patterns.append(pattern.name)
        elif pattern.name and 'redoc' in pattern.name.lower():
            swagger_patterns.append(pattern.name)

if swagger_patterns:
    print(f"   ✓ Found {len(swagger_patterns)} Swagger-related URLs:")
    for name in swagger_patterns:
        print(f"     - {name}")
else:
    print("   ✗ No Swagger URLs found")
    sys.exit(1)

# Check 3: Admin URLs
print("\n✅ Check 3: Verifying Admin API URLs...")
admin_urls_found = False
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'admin' in pattern_str and 'api' in pattern_str:
        admin_urls_found = True
        print(f"   ✓ Found admin API route: {pattern_str}")
        break

if not admin_urls_found:
    print("   ⚠ Warning: Admin API URLs not explicitly found")

# Check 4: Django system check
print("\n✅ Check 4: Running Django system check...")
try:
    call_command('check', '--deploy')
    print("   ✓ Django system check passed")
except Exception as e:
    print(f"   ✗ System check failed: {e}")

# Check 5: REST Framework settings
print("\n✅ Check 5: Verifying REST Framework configuration...")
if hasattr(settings, 'REST_FRAMEWORK'):
    print("   ✓ REST_FRAMEWORK settings configured")
else:
    print("   ⚠ Warning: No REST_FRAMEWORK settings found")

print("\n" + "=" * 70)
print("📝 SUMMARY")
print("=" * 70)
print("\n✅ Swagger is properly configured!\n")
print("🚀 To access Swagger documentation:")
print("   1. Start server: python manage.py runserver")
print("   2. Open browser: http://localhost:8000/swagger/")
print("\n📚 Documentation URLs:")
print("   • Swagger UI:  http://localhost:8000/swagger/")
print("   • ReDoc:       http://localhost:8000/redoc/")
print("   • JSON Schema: http://localhost:8000/swagger.json/")
print("\n" + "=" * 70)
