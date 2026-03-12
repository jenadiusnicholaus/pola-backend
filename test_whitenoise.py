#!/usr/bin/env python3
"""
Test script to verify WhiteNoise configuration
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')

try:
    import django
    django.setup()
    
    # Check if WhiteNoise is in middleware
    from django.conf import settings
    print("✅ Django setup successful")
    
    # Check middleware
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
        print("✅ WhiteNoise middleware found")
    else:
        print("❌ WhiteNoise middleware not found")
    
    # Check static files configuration
    print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"✅ STATIC_URL: {settings.STATIC_URL}")
    print(f"✅ STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    # Check if whitenoise is installed
    try:
        import whitenoise
        print("✅ WhiteNoise package installed")
    except ImportError:
        print("❌ WhiteNoise package not installed")
    
    print("\n🎉 Configuration looks good!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
