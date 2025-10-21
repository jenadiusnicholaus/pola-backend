"""
Management command to seed consultant test data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import PolaUser, Contact
from subscriptions.models import ConsultantProfile, PricingConfiguration
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed consultant test data for admin panel testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding consultant data...\n')
        
        # Create test consultant users if they don't exist
        consultants_data = [
            {
                'email': 'advocate1@example.com',
                'first_name': 'John',
                'last_name': 'Mwangi',
                'phone': '+255712345001',
                'type': 'advocate',
                'specialization': 'Criminal Law, Corporate Law',
                'experience': 10,
                'city': 'Dar es Salaam',
                'offers_mobile': True,
                'offers_physical': True,
            },
            {
                'email': 'advocate2@example.com',
                'first_name': 'Grace',
                'last_name': 'Kimathi',
                'phone': '+255712345002',
                'type': 'advocate',
                'specialization': 'Family Law, Property Law',
                'experience': 7,
                'city': 'Arusha',
                'offers_mobile': True,
                'offers_physical': True,
            },
            {
                'email': 'lawyer1@example.com',
                'first_name': 'David',
                'last_name': 'Nyerere',
                'phone': '+255712345003',
                'type': 'lawyer',
                'specialization': 'Employment Law, Contract Law',
                'experience': 5,
                'city': 'Mwanza',
                'offers_mobile': True,
                'offers_physical': False,
            },
            {
                'email': 'lawyer2@example.com',
                'first_name': 'Sarah',
                'last_name': 'Mkapa',
                'phone': '+255712345004',
                'type': 'lawyer',
                'specialization': 'Real Estate Law, Business Law',
                'experience': 8,
                'city': 'Dodoma',
                'offers_mobile': True,
                'offers_physical': True,
            },
            {
                'email': 'paralegal1@example.com',
                'first_name': 'Peter',
                'last_name': 'Hassan',
                'phone': '+255712345005',
                'type': 'paralegal',
                'specialization': 'Legal Research, Document Preparation',
                'experience': 3,
                'city': 'Dar es Salaam',
                'offers_mobile': True,
                'offers_physical': False,
            },
            {
                'email': 'paralegal2@example.com',
                'first_name': 'Mary',
                'last_name': 'Kenyatta',
                'phone': '+255712345006',
                'type': 'paralegal',
                'specialization': 'Civil Litigation Support, Case Management',
                'experience': 4,
                'city': 'Mbeya',
                'offers_mobile': True,
                'offers_physical': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in consultants_data:
            # Create or get user
            user, user_created = PolaUser.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_active': True,
                }
            )
            
            if user_created:
                user.set_password('Test@123')
                user.save()
                self.stdout.write(f'  ✓ Created user: {user.email}')
            
            # Create contact if doesn't exist
            contact, contact_created = Contact.objects.get_or_create(
                user=user,
                defaults={
                    'phone_number': data['phone'],
                    'phone_is_verified': True,
                }
            )
            
            # Create or update consultant profile
            profile, profile_created = ConsultantProfile.objects.get_or_create(
                user=user,
                defaults={
                    'consultant_type': data['type'],
                    'specialization': data['specialization'],
                    'years_of_experience': data['experience'],
                    'offers_mobile_consultations': data['offers_mobile'],
                    'offers_physical_consultations': data['offers_physical'],
                    'city': data['city'],
                    'is_available': True,
                    'total_consultations': 0,
                    'total_earnings': Decimal('0'),
                    'average_rating': Decimal('4.5'),
                    'total_reviews': 0,
                }
            )
            
            if profile_created:
                created_count += 1
                self.stdout.write(f'  ✓ Created consultant: {profile}')
            else:
                # Update existing profile
                profile.specialization = data['specialization']
                profile.years_of_experience = data['experience']
                profile.city = data['city']
                profile.offers_mobile_consultations = data['offers_mobile']
                profile.offers_physical_consultations = data['offers_physical']
                profile.save()
                updated_count += 1
                self.stdout.write(f'  ✓ Updated consultant: {profile}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'\n✓ Seeding complete!')
        self.stdout.write(f'  - Created: {created_count} consultants')
        self.stdout.write(f'  - Updated: {updated_count} consultants')
        self.stdout.write(f'  - Total: {ConsultantProfile.objects.count()} consultants\n')
        
        # List all consultants
        self.stdout.write('\nAll Consultants:')
        self.stdout.write('-'*60)
        for profile in ConsultantProfile.objects.all().order_by('consultant_type', 'user__first_name'):
            status = '✓ Available' if profile.is_available else '✗ Unavailable'
            services = []
            if profile.offers_mobile_consultations:
                services.append('Mobile')
            if profile.offers_physical_consultations:
                services.append('Physical')
            
            self.stdout.write(
                f'{profile.consultant_type.upper():10} | {profile.user.get_full_name():20} | '
                f'{profile.city:15} | {profile.years_of_experience}y exp | '
                f'{", ".join(services):20} | {status}'
            )
