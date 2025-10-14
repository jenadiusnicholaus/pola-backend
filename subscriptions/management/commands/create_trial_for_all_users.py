"""
Management command to create trial subscriptions for all existing users
Run with: python manage.py create_trial_for_all_users
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import PolaUser
from subscriptions.models import SubscriptionPlan, UserSubscription, Wallet


class Command(BaseCommand):
    help = 'Create trial subscriptions and wallets for all existing users who dont have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating subscriptions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('🔄 CREATING TRIAL SUBSCRIPTIONS FOR ALL USERS'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # Get free trial plan
        try:
            free_trial_plan = SubscriptionPlan.objects.get(plan_type='free_trial')
            self.stdout.write(self.style.SUCCESS(f'✅ Found trial plan: {free_trial_plan.name}'))
            self.stdout.write(f'   Duration: {free_trial_plan.duration_days} day(s)')
            self.stdout.write(f'   Features: Library={free_trial_plan.full_legal_library_access}, '
                            f'Questions={free_trial_plan.monthly_questions_limit}, '
                            f'Forum={free_trial_plan.forum_access}\n')
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Free trial plan not found!'))
            self.stdout.write(self.style.ERROR('   Run: python manage.py seed_subscription_plans'))
            return
        
        # Get all users
        all_users = PolaUser.objects.all()
        self.stdout.write(f'📊 Total users in system: {all_users.count()}\n')
        
        # Statistics
        users_with_subscription = 0
        users_without_subscription = 0
        users_with_wallet = 0
        users_without_wallet = 0
        wallets_created = 0
        subscriptions_created = 0
        
        self.stdout.write(self.style.SUCCESS('Processing users...\n'))
        
        for user in all_users:
            self.stdout.write('-' * 70)
            self.stdout.write(f'👤 User: {user.email} ({user.get_full_name() or "No name"})')
            self.stdout.write(f'   Role: {user.user_role.get_role_display() if user.user_role else "No role"}')
            
            # Check wallet
            has_wallet = hasattr(user, 'wallet')
            if has_wallet:
                users_with_wallet += 1
                self.stdout.write(f'   💰 Wallet: ✅ Exists (Balance: {user.wallet.balance} TZS)')
            else:
                users_without_wallet += 1
                self.stdout.write(f'   💰 Wallet: ❌ Missing')
                
                if not dry_run:
                    # Create wallet
                    Wallet.objects.create(user=user)
                    wallets_created += 1
                    self.stdout.write(self.style.SUCCESS('      ✅ Created wallet'))
                else:
                    self.stdout.write(self.style.WARNING('      Would create wallet'))
            
            # Check subscription
            has_subscription = hasattr(user, 'subscription')
            if has_subscription:
                users_with_subscription += 1
                sub = user.subscription
                self.stdout.write(f'   📋 Subscription: ✅ Exists')
                self.stdout.write(f'      Plan: {sub.plan.name}')
                self.stdout.write(f'      Status: {sub.status}')
                self.stdout.write(f'      Active: {sub.is_active()}')
                self.stdout.write(f'      Trial: {sub.is_trial()}')
                self.stdout.write(f'      Expires: {sub.end_date.strftime("%Y-%m-%d %H:%M")}')
            else:
                users_without_subscription += 1
                self.stdout.write(f'   📋 Subscription: ❌ Missing')
                
                if not dry_run:
                    # Create trial subscription
                    end_date = timezone.now() + timedelta(days=free_trial_plan.duration_days)
                    UserSubscription.objects.create(
                        user=user,
                        plan=free_trial_plan,
                        status='active',
                        end_date=end_date
                    )
                    subscriptions_created += 1
                    self.stdout.write(self.style.SUCCESS(f'      ✅ Created trial subscription'))
                    self.stdout.write(self.style.SUCCESS(f'      Expires: {end_date.strftime("%Y-%m-%d %H:%M")}'))
                else:
                    self.stdout.write(self.style.WARNING('      Would create trial subscription'))
            
            self.stdout.write('')  # Empty line
        
        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('='*70)
        self.stdout.write(f'\n📈 Statistics:')
        self.stdout.write(f'   Total users: {all_users.count()}')
        self.stdout.write(f'   Users with wallets: {users_with_wallet}')
        self.stdout.write(f'   Users without wallets: {users_without_wallet}')
        self.stdout.write(f'   Users with subscriptions: {users_with_subscription}')
        self.stdout.write(f'   Users without subscriptions: {users_without_subscription}')
        
        if not dry_run:
            self.stdout.write(f'\n✅ Actions taken:')
            self.stdout.write(self.style.SUCCESS(f'   Wallets created: {wallets_created}'))
            self.stdout.write(self.style.SUCCESS(f'   Trial subscriptions created: {subscriptions_created}'))
        else:
            self.stdout.write(f'\n⚠️  Actions that would be taken:')
            self.stdout.write(self.style.WARNING(f'   Wallets to create: {users_without_wallet}'))
            self.stdout.write(self.style.WARNING(f'   Trial subscriptions to create: {users_without_subscription}'))
            self.stdout.write(self.style.WARNING('\nRun without --dry-run to actually create them'))
        
        self.stdout.write('\n' + '='*70)
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('🎉 TRIAL SUBSCRIPTIONS CREATED SUCCESSFULLY!'))
        else:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN COMPLETE - No changes made'))
        self.stdout.write('='*70 + '\n')
        
        if not dry_run and subscriptions_created > 0:
            self.stdout.write('\n💡 Next steps:')
            self.stdout.write('   1. Users can now access trial features')
            self.stdout.write('   2. Check user profiles: GET /api/v1/authentication/profile/')
            self.stdout.write('   3. Verify subscription permissions are visible')
            self.stdout.write('   4. Trial expires after 24 hours')
            self.stdout.write('')
