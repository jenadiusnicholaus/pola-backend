"""
Management command to display all current pricing configuration.
Run: python manage.py show_pricing
"""

from django.core.management.base import BaseCommand
from subscriptions.models import PricingConfiguration, CallCreditBundle
from decimal import Decimal


class Command(BaseCommand):
    help = 'Displays all current pricing configurations and call credit bundles'

    def handle(self, *args, **options):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('POLA PLATFORM - COMPLETE PRICING CONFIGURATION'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # Display subscription pricing
        self.stdout.write(self.style.WARNING('1. MONTHLY SUBSCRIPTION'))
        self.stdout.write('   Price: 3,000 TZS/month')
        self.stdout.write('   Revenue Split: 100% Platform')
        self.stdout.write('')
        
        # Display call credit bundles
        self.stdout.write(self.style.WARNING('2. CONSULTATION VOUCHERS (Mobile Legal Consultation)'))
        self.stdout.write('   Revenue Split: 50% Platform / 50% Consultant')
        self.stdout.write('')
        
        bundles = CallCreditBundle.objects.filter(is_active=True).order_by('minutes')
        for bundle in bundles:
            self.stdout.write(
                f'   • {bundle.minutes} min = {int(bundle.price):,} TZS '
                f'({bundle.validity_days} days expiry)'
            )
        self.stdout.write('')
        
        # Display physical consultations
        self.stdout.write(self.style.WARNING('3. PHYSICAL CONSULTATIONS'))
        self.stdout.write('   Revenue Split: 60% Platform / 40% Consultant')
        self.stdout.write('')
        
        physical_types = [
            ('PHYSICAL_ADVOCATE', 'Advocate | Wakili (Can represent in court)'),
            ('PHYSICAL_LAWYER', 'Lawyer | Mwanasheria (Legal advice only)'),
            ('PHYSICAL_PARALEGAL', 'Paralegal | Msaidizi wa Kisheria (Legal advice & reference)'),
        ]
        
        for service_type, description in physical_types:
            try:
                pricing = PricingConfiguration.objects.get(service_type=service_type, is_active=True)
                split = pricing.calculate_split()
                self.stdout.write(
                    f'   • {description}: {int(pricing.price):,} TZS'
                )
                self.stdout.write(
                    f'     - Platform: {int(split["platform"]):,} TZS ({pricing.platform_commission_percent}%)'
                )
                self.stdout.write(
                    f'     - Consultant: {int(split["consultant"]):,} TZS ({pricing.consultant_share_percent}%)'
                )
            except PricingConfiguration.DoesNotExist:
                self.stdout.write(f'   • {description}: NOT CONFIGURED')
        self.stdout.write('')
        
        # Display mobile consultations
        self.stdout.write(self.style.WARNING('4. MOBILE CONSULTATIONS (In-App Calls)'))
        self.stdout.write('   Revenue Split: 50% Platform / 50% Consultant')
        self.stdout.write('   Note: Paid via consultation vouchers above')
        self.stdout.write('')
        
        # Display document generation
        self.stdout.write(self.style.WARNING('5. AUTO-GENERATED DOCUMENTS'))
        self.stdout.write('   Revenue Split: 100% Platform')
        self.stdout.write('')
        
        doc_types = [
            ('DOCUMENT_STANDARD', 'Standard Documents'),
            ('DOCUMENT_ADVANCED', 'Advanced Documents'),
        ]
        
        for service_type, description in doc_types:
            try:
                pricing = PricingConfiguration.objects.get(service_type=service_type, is_active=True)
                self.stdout.write(
                    f'   • {description}: {int(pricing.price):,} TZS'
                )
            except PricingConfiguration.DoesNotExist:
                self.stdout.write(f'   • {description}: NOT CONFIGURED')
        self.stdout.write('')
        
        # Display learning materials
        self.stdout.write(self.style.WARNING('6. LEARNING MATERIALS (Students & Lecturers Hub)'))
        self.stdout.write('')
        
        material_types = [
            ('MATERIAL_STUDENT', 'Student Uploads', '50% Platform / 50% Student'),
            ('MATERIAL_LECTURER', 'Lecturer Uploads', '40% Platform / 60% Lecturer'),
            ('MATERIAL_ADMIN', 'Admin Uploads', '100% Platform'),
        ]
        
        for service_type, description, split_text in material_types:
            try:
                pricing = PricingConfiguration.objects.get(service_type=service_type, is_active=True)
                split = pricing.calculate_split()
                self.stdout.write(
                    f'   • {description}: {int(pricing.price):,} TZS'
                )
                self.stdout.write(
                    f'     - Revenue Split: {split_text}'
                )
                if split['consultant'] > 0:
                    self.stdout.write(
                        f'     - Platform: {int(split["platform"]):,} TZS | '
                        f'Uploader: {int(split["consultant"]):,} TZS'
                    )
            except PricingConfiguration.DoesNotExist:
                self.stdout.write(f'   • {description}: NOT CONFIGURED')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Summary statistics
        total_configs = PricingConfiguration.objects.filter(is_active=True).count()
        total_bundles = CallCreditBundle.objects.filter(is_active=True).count()
        
        self.stdout.write(self.style.SUCCESS(f'SUMMARY:'))
        self.stdout.write(self.style.SUCCESS(f'  - Active Pricing Configurations: {total_configs}'))
        self.stdout.write(self.style.SUCCESS(f'  - Active Call Credit Bundles: {total_bundles}'))
        self.stdout.write(self.style.SUCCESS(f'  - Total Service Types: {total_configs + total_bundles}'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # Revenue split summary
        self.stdout.write(self.style.WARNING('REVENUE SPLIT SUMMARY:'))
        self.stdout.write('')
        self.stdout.write('  Service Category          | Platform | Consultant/Uploader')
        self.stdout.write('  ' + '-' * 76)
        self.stdout.write('  Monthly Subscription      |   100%   |          -')
        self.stdout.write('  Mobile Consultations      |    50%   |        50%')
        self.stdout.write('  Physical Consultations    |    60%   |        40%')
        self.stdout.write('  Student Materials         |    50%   |        50%')
        self.stdout.write('  Lecturer Materials        |    40%   |        60%')
        self.stdout.write('  Admin Materials           |   100%   |         -')
        self.stdout.write('  Generated Documents       |   100%   |         -')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ All pricing configurations are active and ready!'))
        self.stdout.write('')
