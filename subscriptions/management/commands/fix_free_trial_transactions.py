"""
Management command to fix incorrect payment transactions for free trial subscriptions.

Free trial subscriptions should never have payment transactions with non-zero amounts.
This command identifies and fixes such erroneous transactions.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from subscriptions.models import SubscriptionPlan, PaymentTransaction, UserSubscription


class Command(BaseCommand):
    help = 'Fix incorrect payment transactions for free trial subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete the incorrect transactions instead of setting amount to 0',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_transactions = options['delete']

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('FREE TRIAL TRANSACTION FIX'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write()

        # Get free trial plan
        try:
            free_trial_plan = SubscriptionPlan.objects.get(plan_type='free_trial')
            self.stdout.write(f'Found free trial plan: ID {free_trial_plan.id} - {free_trial_plan.name}')
            self.stdout.write(f'Plan price: {free_trial_plan.price} TZS')
            self.stdout.write()
        except SubscriptionPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR('No free trial plan found!'))
            return

        # Find all transactions for free trial subscriptions with non-zero amounts
        incorrect_transactions = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            related_subscription__plan=free_trial_plan
        ).exclude(amount=0)

        total_count = incorrect_transactions.count()
        total_incorrect_amount = sum(t.amount for t in incorrect_transactions)

        self.stdout.write(self.style.WARNING(f'Found {total_count} incorrect transactions'))
        self.stdout.write(self.style.WARNING(f'Total incorrect amount: {total_incorrect_amount:,.2f} TZS'))
        self.stdout.write()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No incorrect transactions found!'))
            return

        # Show sample transactions
        self.stdout.write('Sample incorrect transactions:')
        for t in incorrect_transactions[:10]:
            self.stdout.write(
                f'  - Transaction ID {t.id}: {t.amount} TZS, '
                f'Status: {t.status}, Date: {t.created_at.strftime("%Y-%m-%d")}'
            )
        if total_count > 10:
            self.stdout.write(f'  ... and {total_count - 10} more')
        self.stdout.write()

        # Breakdown by status
        completed = incorrect_transactions.filter(status='completed').count()
        pending = incorrect_transactions.filter(status='pending').count()
        failed = incorrect_transactions.filter(status='failed').count()
        
        self.stdout.write('Breakdown by status:')
        self.stdout.write(f'  - Completed: {completed}')
        self.stdout.write(f'  - Pending: {pending}')
        self.stdout.write(f'  - Failed: {failed}')
        self.stdout.write()

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            if delete_transactions:
                self.stdout.write(self.style.WARNING('Would DELETE these transactions'))
            else:
                self.stdout.write(self.style.WARNING('Would SET amount to 0 for these transactions'))
            return

        # Ask for confirmation
        self.stdout.write(self.style.WARNING('⚠️  WARNING: This will modify database records'))
        if delete_transactions:
            self.stdout.write(self.style.WARNING(f'This will DELETE {total_count} transactions'))
        else:
            self.stdout.write(self.style.WARNING(f'This will set amount to 0 for {total_count} transactions'))
        
        confirm = input('Are you sure you want to continue? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Operation cancelled'))
            return

        # Perform the fix
        self.stdout.write()
        self.stdout.write('Processing...')
        
        if delete_transactions:
            deleted_count = incorrect_transactions.delete()[0]
            self.stdout.write()
            self.stdout.write(self.style.SUCCESS(f'✓ Deleted {deleted_count} transactions'))
        else:
            updated_count = 0
            for transaction in incorrect_transactions:
                old_amount = transaction.amount
                transaction.amount = 0
                transaction.save()
                updated_count += 1
                if updated_count % 10 == 0:
                    self.stdout.write(f'  Processed {updated_count}/{total_count}...')
            
            self.stdout.write()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated {updated_count} transactions to amount 0'))

        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('FIX COMPLETED SUCCESSFULLY'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Verify the fix
        remaining = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            related_subscription__plan=free_trial_plan
        ).exclude(amount=0).count()
        
        if remaining == 0:
            self.stdout.write(self.style.SUCCESS('✓ Verification: No incorrect transactions remaining'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Warning: {remaining} incorrect transactions still exist'))
