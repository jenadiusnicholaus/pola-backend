"""
Script to list all registered public API endpoints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.urls import get_resolver
from rest_framework.routers import DefaultRouter

def list_endpoints():
    """List all URL patterns"""
    resolver = get_resolver()
    
    print("=" * 80)
    print("PHASE 3: PUBLIC API ENDPOINTS")
    print("=" * 80)
    print()
    
    # Get subscriptions URLs
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'pattern') and 'api/v1/subscriptions' in str(pattern.pattern):
            if hasattr(pattern, 'url_patterns'):
                for sub_pattern in pattern.url_patterns:
                    if hasattr(sub_pattern, 'pattern'):
                        url = f"/api/v1/subscriptions/{sub_pattern.pattern}"
                        # Filter for new endpoints
                        if any(keyword in str(url) for keyword in [
                            'pricing', 'call-credit', 'consultant', 
                            'consultation', 'payment', 'earnings'
                        ]):
                            print(f"✅ {url}")
    
    print()
    print("=" * 80)
    print("ENDPOINT CATEGORIES:")
    print("=" * 80)
    print()
    print("📊 PRICING:")
    print("   GET  /api/v1/subscriptions/pricing/")
    print("   GET  /api/v1/subscriptions/pricing/{id}/")
    print("   GET  /api/v1/subscriptions/pricing/by-service/?type=mobile_consultation")
    print()
    print("💳 CALL CREDITS:")
    print("   GET  /api/v1/subscriptions/call-credits/bundles/")
    print("   GET  /api/v1/subscriptions/call-credits/{id}/")
    print("   POST /api/v1/subscriptions/call-credits/purchase/")
    print("   GET  /api/v1/subscriptions/call-credits/my-balance/")
    print()
    print("👨‍⚖️ CONSULTANTS:")
    print("   GET  /api/v1/subscriptions/consultants/")
    print("   GET  /api/v1/subscriptions/consultants/{id}/")
    print("   POST /api/v1/subscriptions/consultants/register/")
    print("   GET  /api/v1/subscriptions/consultants/my-profile/")
    print("   GET  /api/v1/subscriptions/consultants/search/?specialization=criminal")
    print()
    print("📅 CONSULTATIONS:")
    print("   POST /api/v1/subscriptions/consultations/book/")
    print("   GET  /api/v1/subscriptions/consultations/")
    print("   GET  /api/v1/subscriptions/consultations/{id}/")
    print("   PATCH /api/v1/subscriptions/consultations/{id}/cancel/")
    print("   POST /api/v1/subscriptions/consultations/{id}/start-call/")
    print("   POST /api/v1/subscriptions/consultations/{id}/end-call/")
    print("   POST /api/v1/subscriptions/consultations/{id}/rate/")
    print()
    print("💰 PAYMENTS:")
    print("   GET  /api/v1/subscriptions/payments/")
    print("   GET  /api/v1/subscriptions/payments/{id}/")
    print("   POST /api/v1/subscriptions/payments/initiate/")
    print("   GET  /api/v1/subscriptions/payments/{id}/status/")
    print()
    print("💵 EARNINGS:")
    print("   GET  /api/v1/subscriptions/earnings/consultant/")
    print("   GET  /api/v1/subscriptions/earnings/uploader/")
    print("   GET  /api/v1/subscriptions/earnings/summary/")
    print()
    print("=" * 80)
    print("TOTAL NEW ENDPOINTS: 26+")
    print("=" * 80)

if __name__ == '__main__':
    list_endpoints()
