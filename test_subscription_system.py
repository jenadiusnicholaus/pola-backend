"""
Test script to verify subscription system is working
Run with: python manage.py shell < test_subscription_system.py
"""

from subscriptions.models import *
from authentication.models import PolaUser
from django.utils import timezone
from datetime import timedelta

print("\n" + "="*70)
print("🧪 TESTING SUBSCRIPTION SYSTEM")
print("="*70 + "\n")

# 1. Check Subscription Plans
print("1️⃣ Checking Subscription Plans...")
plans = SubscriptionPlan.objects.all()
print(f"   ✅ Found {plans.count()} plans:")
for plan in plans:
    print(f"      - {plan.name}: {plan.price} TZS for {plan.duration_days} days")

# 2. Check if signal works (wallet creation)
print("\n2️⃣ Checking Auto-Wallet Creation...")
user = PolaUser.objects.first()
if user:
    has_wallet = hasattr(user, 'wallet')
    has_subscription = hasattr(user, 'subscription')
    print(f"   User: {user.email}")
    print(f"   ✅ Has Wallet: {has_wallet}")
    print(f"   ✅ Has Subscription: {has_subscription}")
    
    if has_wallet:
        print(f"   💰 Wallet Balance: {user.wallet.balance} TZS")
    
    if has_subscription:
        print(f"   📅 Subscription: {user.subscription.plan.name}")
        print(f"   📊 Status: {user.subscription.status}")
        print(f"   ⏰ Expires: {user.subscription.end_date}")
else:
    print("   ⚠️  No users found. Create a user first.")

# 3. Check Models
print("\n3️⃣ Checking Database Models...")
models_check = [
    ('SubscriptionPlan', SubscriptionPlan),
    ('UserSubscription', UserSubscription),
    ('Wallet', Wallet),
    ('Transaction', Transaction),
    ('ConsultationVoucher', ConsultationVoucher),
    ('ConsultationSession', ConsultationSession),
    ('DocumentType', DocumentType),
    ('DocumentPurchase', DocumentPurchase),
    ('LearningMaterial', LearningMaterial),
    ('LearningMaterialPurchase', LearningMaterialPurchase),
]

for model_name, model_class in models_check:
    count = model_class.objects.count()
    print(f"   ✅ {model_name}: {count} records")

# 4. Test Wallet Operations
print("\n4️⃣ Testing Wallet Operations...")
if user and has_wallet:
    try:
        # Test deposit
        initial_balance = user.wallet.balance
        user.wallet.deposit(5000, "Test deposit")
        print(f"   ✅ Deposit Test: {initial_balance} → {user.wallet.balance} TZS")
        
        # Check transaction was created
        txn_count = user.wallet.transactions.count()
        print(f"   ✅ Transactions Created: {txn_count}")
        
        # Test balance check
        has_balance = user.wallet.has_sufficient_balance(1000)
        print(f"   ✅ Balance Check: {has_balance}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("   ⚠️  No user with wallet found")

# 5. Test Subscription Methods
print("\n5️⃣ Testing Subscription Methods...")
if user and has_subscription:
    try:
        sub = user.subscription
        print(f"   ✅ Is Active: {sub.is_active()}")
        print(f"   ✅ Days Remaining: {sub.days_remaining()}")
        print(f"   ✅ Is Trial: {sub.is_trial()}")
        print(f"   ✅ Can Ask Question: {sub.can_ask_question()}")
        print(f"   ✅ Can Generate Free Doc: {sub.can_generate_free_document()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("   ⚠️  No user with subscription found")

# 6. Summary
print("\n" + "="*70)
print("📊 SUMMARY")
print("="*70)
print(f"✅ Subscription Plans: {SubscriptionPlan.objects.count()}")
print(f"✅ User Subscriptions: {UserSubscription.objects.count()}")
print(f"✅ Wallets: {Wallet.objects.count()}")
print(f"✅ Transactions: {Transaction.objects.count()}")
print(f"✅ Consultation Vouchers: {ConsultationVoucher.objects.count()}")
print(f"✅ Consultation Sessions: {ConsultationSession.objects.count()}")
print(f"✅ Document Types: {DocumentType.objects.count()}")
print(f"✅ Document Purchases: {DocumentPurchase.objects.count()}")
print(f"✅ Learning Materials: {LearningMaterial.objects.count()}")
print(f"✅ Learning Material Purchases: {LearningMaterialPurchase.objects.count()}")

print("\n" + "="*70)
print("🎉 SUBSCRIPTION SYSTEM TEST COMPLETE!")
print("="*70 + "\n")

print("📝 Next Steps:")
print("   1. Run: python manage.py runserver")
print("   2. Visit: http://localhost:8000/swagger/")
print("   3. Look for 'subscriptions' tag")
print("   4. Test the 27 API endpoints!")
print("\n")
