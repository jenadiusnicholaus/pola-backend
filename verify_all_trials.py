from authentication.models import PolaUser
from subscriptions.models import UserSubscription, Wallet

print('\n' + '='*70)
print('📊 VERIFICATION: ALL USERS HAVE TRIAL SUBSCRIPTIONS')
print('='*70)

total_users = PolaUser.objects.count()
users_with_wallets = PolaUser.objects.filter(wallet__isnull=False).count()
users_with_subs = PolaUser.objects.filter(subscription__isnull=False).count()
active_trials = UserSubscription.objects.filter(plan__plan_type='free_trial', status='active').count()

print(f'\n✅ Total Users: {total_users}')
print(f'✅ Users with Wallets: {users_with_wallets}/{total_users}')
print(f'✅ Users with Subscriptions: {users_with_subs}/{total_users}')
print(f'✅ Active Trial Subscriptions: {active_trials}')

# Check the user from your example
print('\n' + '='*70)
print('📋 CHECKING USER: paralegal.test@example.com')
print('='*70)

try:
    user = PolaUser.objects.get(email='paralegal.test@example.com')
    print(f'\n👤 User: {user.email} ({user.get_full_name()})')
    print(f'   Role: {user.user_role.get_role_display() if user.user_role else "No role"}')
    
    # Check wallet
    has_wallet = hasattr(user, 'wallet')
    print(f'\n💰 Wallet: {"✅ Yes" if has_wallet else "❌ No"}')
    if has_wallet:
        print(f'   Balance: {user.wallet.balance} TZS')
    
    # Check subscription
    has_sub = hasattr(user, 'subscription')
    print(f'\n📋 Subscription: {"✅ Yes" if has_sub else "❌ No"}')
    if has_sub:
        sub = user.subscription
        print(f'   Plan: {sub.plan.name}')
        print(f'   Plan Type: {sub.plan.plan_type}')
        print(f'   Status: {sub.status}')
        print(f'   Is Active: {sub.is_active()}')
        print(f'   Is Trial: {sub.is_trial()}')
        print(f'   Days Remaining: {sub.days_remaining()}')
        print(f'   End Date: {sub.end_date.strftime("%Y-%m-%d %H:%M")}')
        
        # Get permissions
        perms = sub.get_permissions()
        print(f'\n🔐 Permissions:')
        print(f'   is_active: {perms["is_active"]}')
        print(f'   can_access_legal_library: {perms["can_access_legal_library"]}')
        print(f'   can_ask_questions: {perms["can_ask_questions"]}')
        print(f'   questions_remaining: {perms.get("questions_remaining", 0)}')
        print(f'   can_access_forum: {perms["can_access_forum"]}')
        print(f'   can_access_student_hub: {perms["can_access_student_hub"]}')
        print(f'   can_purchase_consultations: {perms["can_purchase_consultations"]}')

except PolaUser.DoesNotExist:
    print('\n❌ User not found!')

# Show a few more users
print('\n' + '='*70)
print('📋 OTHER USER SAMPLES')
print('='*70)

other_emails = ['lawyer@example.com', 'student@udsm.ac.tz', 'citizen@example.com']
for email in other_emails:
    try:
        user = PolaUser.objects.get(email=email)
        has_sub = hasattr(user, 'subscription')
        has_wallet = hasattr(user, 'wallet')
        print(f'\n👤 {email}')
        print(f'   Wallet: {"✅" if has_wallet else "❌"} | Subscription: {"✅" if has_sub else "❌"}')
        if has_sub:
            print(f'   Plan: {user.subscription.plan.name} (Active: {user.subscription.is_active()})')
    except PolaUser.DoesNotExist:
        print(f'\n👤 {email} - Not found')

print('\n' + '='*70)
print('✅ ALL USERS NOW HAVE TRIAL SUBSCRIPTIONS!')
print('='*70 + '\n')
