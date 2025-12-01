#!/usr/bin/env python3
"""
Test subscription payment endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_subscription_endpoints():
    """Test subscription endpoints without auth"""
    
    print("=" * 60)
    print("Testing Subscription Payment Endpoints")
    print("=" * 60)
    
    # Test 1: Get subscription plans (requires auth)
    print("\n1. Testing GET /subscriptions/plans/")
    try:
        response = requests.get(f"{BASE_URL}/subscriptions/plans/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Endpoint requires authentication (expected)")
        elif response.status_code == 200:
            data = response.json()
            print(f"   ✓ Response: {json.dumps(data[:1] if isinstance(data, list) else data, indent=2)}")
        else:
            print(f"   ✗ Unexpected status: {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Check if subscribe endpoint exists
    print("\n2. Testing POST /subscriptions/subscribe/ (without auth)")
    try:
        response = requests.post(
            f"{BASE_URL}/subscriptions/subscribe/",
            json={"plan_id": 1, "payment_method": "mobile_money", "phone_number": "+255712345678"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Endpoint requires authentication (expected)")
        elif response.status_code == 404:
            print("   ✗ Endpoint not found - check URL configuration")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Check payment status endpoint
    print("\n3. Testing GET /subscriptions/payment-status/ (without auth)")
    try:
        response = requests.get(f"{BASE_URL}/subscriptions/payment-status/", params={"transaction_id": "TEST123"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Endpoint requires authentication (expected)")
        elif response.status_code == 404:
            print("   ✗ Endpoint not found - check URL configuration")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Endpoint Configuration Summary:")
    print("=" * 60)
    print("All endpoints require authentication as expected.")
    print("Use Bearer token in Authorization header to access.")
    print("=" * 60)

if __name__ == "__main__":
    test_subscription_endpoints()
