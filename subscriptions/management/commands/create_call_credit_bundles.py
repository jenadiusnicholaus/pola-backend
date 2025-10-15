"""
Management command to create call credit bundles (consultation vouchers).
Run this after migrations: python manage.py create_call_credit_bundles
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from subscriptions.models import CallCreditBundle


class Command(BaseCommand):
    help = 'Creates call credit bundles for mobile consultations (consultation vouchers)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating call credit bundles...'))
        
        # Define all call credit bundles based on requirements
        bundles_data = [
            {
                'name': '5 Minutes Bundle',
                'minutes': 5,
                'price': Decimal('3000.00'),
                'validity_days': 3,
            },
            {
                'name': '10 Minutes Bundle',
                'minutes': 10,
                'price': Decimal('5000.00'),
                'validity_days': 5,
            },
            {
                'name': '20 Minutes Bundle',
                'minutes': 20,
                'price': Decimal('9000.00'),
                'validity_days': 7,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in bundles_data:
            bundle, created = CallCreditBundle.objects.update_or_create(
                minutes=data['minutes'],
                defaults={
                    'name': data['name'],
                    'price': data['price'],
                    'validity_days': data['validity_days'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {data["name"]} - {data["minutes"]} min = {data["price"]} TZS '
                        f'({data["validity_days"]} days expiry)'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'↻ Updated: {data["name"]} - {data["minutes"]} min = {data["price"]} TZS '
                        f'({data["validity_days"]} days expiry)'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  - Created: {created_count} bundles'))
        self.stdout.write(self.style.SUCCESS(f'  - Updated: {updated_count} bundles'))
        self.stdout.write(self.style.SUCCESS(f'  - Total: {created_count + updated_count} bundles'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✓ Call credit bundles created successfully!')
        )
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Note: Users can carry forward unused minutes within the validity period.'))
