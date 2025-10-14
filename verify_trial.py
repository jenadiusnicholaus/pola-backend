from subscriptions.models import SubscriptionPlan

trial = SubscriptionPlan.objects.get(plan_type='free_trial')
monthly = SubscriptionPlan.objects.get(plan_type='monthly')

print('\n' + '='*70)
print('🔐 UPDATED FREE TRIAL PERMISSIONS')
print('='*70 + '\n')

print('📋 FREE TRIAL (24 Hours) - 0 TZS')
print('-' * 70)
trial_perms = trial.get_permissions()
for key, value in trial_perms.items():
    icon = '✅' if value else '❌'
    if isinstance(value, bool):
        print(f'   {icon} {key}: {value}')
    else:
        print(f'   📊 {key}: {value}')

print('\n📋 MONTHLY SUBSCRIPTION - 3,000 TZS')
print('-' * 70)
monthly_perms = monthly.get_permissions()
for key, value in monthly_perms.items():
    icon = '✅' if value else '❌'
    if isinstance(value, bool):
        print(f'   {icon} {key}: {value}')
    else:
        print(f'   📊 {key}: {value}')

print('\n' + '='*70)
print('✅ Trial users can now:')
print('   • Browse legal library')
print('   • Ask 5 questions')
print('   • Access forums')
print('   • Access student hub')
print('   • Purchase consultations, documents, and materials')
print('\n🎯 Perfect for testing the platform!')
print('='*70 + '\n')
