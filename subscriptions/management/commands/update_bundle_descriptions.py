"""
Management command to update CallCreditBundle descriptions
"""
from django.core.management.base import BaseCommand
from subscriptions.models import CallCreditBundle


class Command(BaseCommand):
    help = 'Update CallCreditBundle descriptions'

    def handle(self, *args, **kwargs):
        self.stdout.write('Updating bundle descriptions...\n')
        
        # Update 30 Minutes bundle to BRONZE (5 min, 3000 TZS)
        try:
            bundle_30 = CallCreditBundle.objects.get(name="30 Minutes")
            bundle_30.name = "BRONZE"
            bundle_30.name_sw = "SHABA"
            bundle_30.minutes = 5
            bundle_30.price = 3000
            bundle_30.validity_days = 3
            bundle_30.description = "Bronze package - Perfect for quick legal consultations. Get 5 minutes of mobile consultation time with experienced legal professionals."
            bundle_30.description_sw = "Kifurushi cha Shaba - Bora kwa ushauri wa haraka wa kisheria. Pata dakika 5 za mazungumzo ya simu na wataalam wa sheria wenye uzoefu."
            bundle_30.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated: {bundle_30.name} / {bundle_30.name_sw}'))
        except CallCreditBundle.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ 30 Minutes bundle not found, creating BRONZE...'))
            CallCreditBundle.objects.create(
                name="BRONZE",
                name_sw="SHABA",
                minutes=5,
                price=3000,
                validity_days=3,
                description="Bronze package - Perfect for quick legal consultations. Get 5 minutes of mobile consultation time with experienced legal professionals.",
                description_sw="Kifurushi cha Shaba - Bora kwa ushauri wa haraka wa kisheria. Pata dakika 5 za mazungumzo ya simu na wataalam wa sheria wenye uzoefu.",
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('✓ Created: BRONZE / SHABA'))
        
        # Update 60 Minutes bundle to SILVER (10 min, 5000 TZS)
        try:
            bundle_60 = CallCreditBundle.objects.get(name="60 Minutes")
            bundle_60.name = "SILVER"
            bundle_60.name_sw = "FEDHA"
            bundle_60.minutes = 10
            bundle_60.price = 5000
            bundle_60.validity_days = 5
            bundle_60.description = "Silver package - Ideal for in-depth legal discussions. Get 10 minutes to thoroughly discuss your legal matters with qualified consultants."
            bundle_60.description_sw = "Kifurushi cha Fedha - Bora kwa majadiliano ya kina ya kisheria. Pata dakika 10 za kujadili kwa kina masuala yako ya kisheria na washauri wenye sifa."
            bundle_60.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated: {bundle_60.name} / {bundle_60.name_sw}'))
        except CallCreditBundle.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ 60 Minutes bundle not found, creating SILVER...'))
            CallCreditBundle.objects.create(
                name="SILVER",
                name_sw="FEDHA",
                minutes=10,
                price=5000,
                validity_days=5,
                description="Silver package - Ideal for in-depth legal discussions. Get 10 minutes to thoroughly discuss your legal matters with qualified consultants.",
                description_sw="Kifurushi cha Fedha - Bora kwa majadiliano ya kina ya kisheria. Pata dakika 10 za kujadili kwa kina masuala yako ya kisheria na washauri wenye sifa.",
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('✓ Created: SILVER / FEDHA'))
        
        # Update 120 Minutes bundle to GOLD (20 min, 9000 TZS)
        try:
            bundle_120 = CallCreditBundle.objects.get(name="120 Minutes")
            bundle_120.name = "GOLD"
            bundle_120.name_sw = "DHAHABU"
            bundle_120.minutes = 20
            bundle_120.price = 9000
            bundle_120.validity_days = 7
            bundle_120.description = "Gold package - Best value for comprehensive legal guidance. Get 20 minutes for extensive legal consultations and detailed advice."
            bundle_120.description_sw = "Kifurushi cha Dhahabu - Thamani bora kwa mwongozo kamili wa kisheria. Pata dakika 20 kwa ushauri mkubwa wa kisheria na miongozo ya kina."
            bundle_120.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Updated: {bundle_120.name} / {bundle_120.name_sw}'))
        except CallCreditBundle.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ 120 Minutes bundle not found, creating GOLD...'))
            CallCreditBundle.objects.create(
                name="GOLD",
                name_sw="DHAHABU",
                minutes=20,
                price=9000,
                validity_days=7,
                description="Gold package - Best value for comprehensive legal guidance. Get 20 minutes for extensive legal consultations and detailed advice.",
                description_sw="Kifurushi cha Dhahabu - Thamani bora kwa mwongozo kamili wa kisheria. Pata dakika 20 kwa ushauri mkubwa wa kisheria na miongozo ya kina.",
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('✓ Created: GOLD / DHAHABU'))
        
        # Display all bundles
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\nAll Call Credit Bundles:\n'))
        for bundle in CallCreditBundle.objects.all():
            self.stdout.write(f'\n{bundle.name} / {bundle.name_sw}:')
            self.stdout.write(f'  Description: {bundle.description}')
            self.stdout.write(f'  Description (SW): {bundle.description_sw}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✓ Bundle names and descriptions updated successfully!'))
