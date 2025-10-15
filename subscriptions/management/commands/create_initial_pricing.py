"""
Management command to create initial pricing configuration for all service types.
Run this after migrations: python manage.py create_initial_pricing
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from subscriptions.models import PricingConfiguration


class Command(BaseCommand):
    help = 'Creates initial pricing configuration for all service types'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating initial pricing configurations...'))
        
        # Define all service types with their prices (in TZS) and revenue splits
        pricing_data = [
            # Mobile Consultations (50/50 split - App/Consultant)
            {
                'service_type': 'MOBILE_ADVOCATE',
                'price': Decimal('0.00'),  # Paid via call credit bundles
                'platform_commission_percent': Decimal('50.00'),
                'consultant_share_percent': Decimal('50.00'),
                'description': 'Mobile consultation with advocate via in-app call (50/50 split)',
            },
            {
                'service_type': 'MOBILE_LAWYER',
                'price': Decimal('0.00'),  # Paid via call credit bundles
                'platform_commission_percent': Decimal('50.00'),
                'consultant_share_percent': Decimal('50.00'),
                'description': 'Mobile consultation with lawyer via in-app call (50/50 split)',
            },
            {
                'service_type': 'MOBILE_PARALEGAL',
                'price': Decimal('0.00'),  # Paid via call credit bundles
                'platform_commission_percent': Decimal('50.00'),
                'consultant_share_percent': Decimal('50.00'),
                'description': 'Mobile consultation with paralegal via in-app call (50/50 split)',
            },
            
            # Physical Consultations (60/40 split - App/Consultant)
            {
                'service_type': 'PHYSICAL_ADVOCATE',
                'price': Decimal('60000.00'),
                'platform_commission_percent': Decimal('60.00'),
                'consultant_share_percent': Decimal('40.00'),
                'description': 'Physical consultation with advocate (60/40 split)',
            },
            {
                'service_type': 'PHYSICAL_LAWYER',
                'price': Decimal('35000.00'),
                'platform_commission_percent': Decimal('60.00'),
                'consultant_share_percent': Decimal('40.00'),
                'description': 'Physical consultation with lawyer (60/40 split)',
            },
            {
                'service_type': 'PHYSICAL_PARALEGAL',
                'price': Decimal('25000.00'),
                'platform_commission_percent': Decimal('60.00'),
                'consultant_share_percent': Decimal('40.00'),
                'description': 'Physical consultation with paralegal (60/40 split)',
            },
            
            # Document Generation
            {
                'service_type': 'DOCUMENT_STANDARD',
                'price': Decimal('5000.00'),
                'platform_commission_percent': Decimal('100.00'),
                'consultant_share_percent': Decimal('0.00'),
                'description': 'Standard auto-generated legal document',
            },
            {
                'service_type': 'DOCUMENT_ADVANCED',
                'price': Decimal('15000.00'),
                'platform_commission_percent': Decimal('100.00'),
                'consultant_share_percent': Decimal('0.00'),
                'description': 'Advanced auto-generated legal document',
            },
            
            # Learning Materials
            {
                'service_type': 'MATERIAL_STUDENT',
                'price': Decimal('1500.00'),
                'platform_commission_percent': Decimal('50.00'),
                'consultant_share_percent': Decimal('50.00'),
                'description': 'Study material uploaded by student (50/50 split)',
            },
            {
                'service_type': 'MATERIAL_LECTURER',
                'price': Decimal('5000.00'),
                'platform_commission_percent': Decimal('40.00'),
                'consultant_share_percent': Decimal('60.00'),
                'description': 'Study material uploaded by lecturer (40/60 split - 60% to lecturer)',
            },
            {
                'service_type': 'MATERIAL_ADMIN',
                'price': Decimal('3000.00'),
                'platform_commission_percent': Decimal('100.00'),
                'consultant_share_percent': Decimal('0.00'),
                'description': 'Study material uploaded by admin (100% platform)',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in pricing_data:
            config, created = PricingConfiguration.objects.update_or_create(
                service_type=data['service_type'],
                defaults={
                    'price': data['price'],
                    'description': data['description'],
                    'platform_commission_percent': data['platform_commission_percent'],
                    'consultant_share_percent': data['consultant_share_percent'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {data["service_type"]} - {data["price"]} TZS '
                        f'(Platform: {data["platform_commission_percent"]}% / '
                        f'Consultant: {data["consultant_share_percent"]}%)'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'↻ Updated: {data["service_type"]} - {data["price"]} TZS '
                        f'(Platform: {data["platform_commission_percent"]}% / '
                        f'Consultant: {data["consultant_share_percent"]}%)'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  - Created: {created_count} configurations'))
        self.stdout.write(self.style.SUCCESS(f'  - Updated: {updated_count} configurations'))
        self.stdout.write(self.style.SUCCESS(f'  - Total: {created_count + updated_count} configurations'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✓ Initial pricing configuration completed successfully!')
        )
        
        # Display revenue split examples
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Revenue Split Examples (60% Platform / 40% Consultant):'))
        self.stdout.write(self.style.WARNING('-' * 70))
        
        for data in pricing_data:
            if data['service_type'] in ['MOBILE_ADVOCATE', 'MOBILE_LAWYER', 'MOBILE_PARALEGAL', 'PHYSICAL_CONSULTATION']:
                price = data['price']
                platform = price * Decimal('0.60')
                consultant = price * Decimal('0.40')
                self.stdout.write(
                    f"  {data['service_type']:25} | "
                    f"Price: {price:>10} TZS | "
                    f"Platform: {platform:>10} TZS | "
                    f"Consultant: {consultant:>10} TZS"
                )
