"""
Test script to verify subscription permissions system
Run with: python manage.py shell < test_permissions.py
"""

print("\n" + "="*60)
print("🔐 TESTING SUBSCRIPTION PERMISSIONS SYSTEM")
print("="*60 + "\n")

from authentication.models import PolaUser
from subscriptions.models import SubscriptionPlan, UserSubscription
from django.utils import timezone
from datetime import timedelta

# Test 1: Check subscription plans have permissions
print("📋 TEST 1: Check Subscription Plans")
print("-" * 60)
plans = SubscriptionPlan.objects.all()
for plan in plans:
    print(f"\n✅ Plan: {plan.name}")
    print(f"   Price: {plan.price} TZS")
    print(f"   Duration: {plan.duration_days} days")
    
    permissions = plan.get_permissions()
    print(f"   Permissions:")
    for key, value in permissions.items():
        print(f"      - {key}: {value}")

# Test 2: Check if new users get trial subscription
print("\n\n📋 TEST 2: Check User Subscriptions")
print("-" * 60)
users_list = list(PolaUser.objects.all()[:5])
for user in users_list:
    print(f"\n✅ User: {user.email}")
    
    try:
        subscription = user.subscription
        print(f"   Has Subscription: True")
        print(f"   Plan: {subscription.plan.name}")
        print(f"   Status: {subscription.status}")
        print(f"   Is Active: {subscription.is_active()}")
        print(f"   Is Trial: {subscription.is_trial()}")
        print(f"   Days Remaining: {subscription.days_remaining()}")
        
        # Test permissions
        permissions = subscription.get_permissions()
        print(f"   Key Permissions:")
        print(f"      - is_active: {permissions['is_active']}")
        print(f"      - can_ask_questions: {permissions['can_ask_questions']}")
        print(f"      - questions_remaining: {permissions.get('questions_remaining', 'N/A')}")
        print(f"      - can_generate_documents: {permissions['can_generate_documents']}")
        print(f"      - documents_remaining: {permissions['documents_remaining']}")
        
    except UserSubscription.DoesNotExist:
        print(f"   Has Subscription: False")
        print(f"   ⚠️  Note: User created before signals were set up")

# Test 3: Test permission methods
print("\n\n📋 TEST 3: Test Permission Checking Functions")
print("-" * 60)

from subscriptions.permissions import (
    get_user_subscription_permissions,
    check_subscription_permission,
    check_questions_limit,
    check_documents_limit
)

if users_list:
    test_user = users_list[0]
    print(f"\n✅ Testing with user: {test_user.email}")
    
    # Get all permissions
    perms = get_user_subscription_permissions(test_user)
    print(f"\n   All Permissions:")
    for key, value in perms.items():
        print(f"      - {key}: {value}")
    
    # Check specific permissions
    print(f"\n   Permission Checks:")
    print(f"      - Can access legal library: {check_subscription_permission(test_user, 'can_access_legal_library')}")
    print(f"      - Can access forum: {check_subscription_permission(test_user, 'can_access_forum')}")
    print(f"      - Can access student hub: {check_subscription_permission(test_user, 'can_access_student_hub')}")
    
    # Check limits
    try:
        can_ask, remaining_questions = check_questions_limit(test_user)
        print(f"\n   Question Limit:")
        print(f"      - Can ask: {can_ask}")
        print(f"      - Remaining: {remaining_questions}")
        
        can_generate, remaining_docs = check_documents_limit(test_user)
        print(f"\n   Document Limit:")
        print(f"      - Can generate free: {can_generate}")
        print(f"      - Remaining: {remaining_docs}")
    except Exception as e:
        print(f"      ⚠️  Error checking limits: {e}")

# Test 4: Test serializer integration
print("\n\n📋 TEST 4: Test Serializer Integration")
print("-" * 60)

from subscriptions.serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer
)

# Test plan serializer
if plans.exists():
    plan = plans.first()
    plan_data = SubscriptionPlanSerializer(plan).data
    print(f"\n✅ SubscriptionPlan Serializer Output:")
    print(f"   ID: {plan_data['id']}")
    print(f"   Name: {plan_data['name']}")
    print(f"   Has 'permissions' field: {'permissions' in plan_data}")
    if 'permissions' in plan_data:
        print(f"   Permissions keys: {list(plan_data['permissions'].keys())}")

# Test user subscription serializer
if users_list:
    user = users_list[0]
    try:
        subscription = user.subscription
        sub_data = UserSubscriptionSerializer(subscription).data
        print(f"\n✅ UserSubscription Serializer Output:")
        print(f"   ID: {sub_data['id']}")
        print(f"   Plan: {sub_data['plan']}")
        print(f"   Status: {sub_data['status']}")
        print(f"   Has 'permissions' field: {'permissions' in sub_data}")
        if 'permissions' in sub_data:
            print(f"   Permissions keys: {list(sub_data['permissions'].keys())}")
    except:
        print(f"   ⚠️  No subscription for this user")

# Test 5: Summary
print("\n\n📊 SUMMARY")
print("="*60)
print(f"✅ Total Subscription Plans: {plans.count()}")

total_users = PolaUser.objects.count()
print(f"✅ Total Users: {total_users}")

users_with_subs = PolaUser.objects.filter(subscription__isnull=False).count()
print(f"✅ Users with Subscriptions: {users_with_subs}")

active_subs = UserSubscription.objects.filter(status='active').count()
expired_subs = UserSubscription.objects.filter(status='expired').count()
print(f"✅ Active Subscriptions: {active_subs}")
print(f"✅ Expired Subscriptions: {expired_subs}")

print("\n" + "="*60)
print("🎉 PERMISSION SYSTEM TEST COMPLETE!")
print("="*60 + "\n")

print("\n💡 NEXT STEPS:")
print("   1. Start server: python manage.py runserver")
print("   2. Test profile API: GET /api/v1/authentication/profile/")
print("   3. Check 'subscription' field in response")
print("   4. Verify 'permissions' object is present")
print("   5. Frontend can use permissions to control UI")
print("\n")
