# authentication/management/commands/seed_legal_professionals.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.device_models import UserDevice
from authentication.models import UserRole, Contact, Address, Region, District, Specialization, ProfessionalSpecialization
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed sample legal professionals with devices in Dar es Salaam for testing nearby search'

    def handle(self, *args, **kwargs):
        # Sample data with Dar es Salaam coordinates
        legal_professionals = [
            # Advocates
            {
                'email': 'advocate1@pola.test',
                'first_name': 'John',
                'last_name': 'Mwakasege',
                'user_type': 'advocate',
                'latitude': -6.7924,
                'longitude': 39.2083,
                'phone': '+255712345001',
                'location': 'City Centre, Dar es Salaam',
                'years_of_experience': 15,
                'practice_status': 'active',
                'bar_membership_number': 'TLS-2008-001234',
                'roll_number': 'ADV-001234',
                'office_address': '123 Samora Avenue, City Centre',
                'ward': 'Kivukoni',
                'specializations': ['Criminal Law', 'Family Law']
            },
            {
                'email': 'advocate2@pola.test',
                'first_name': 'Mary',
                'last_name': 'Kimaro',
                'user_type': 'advocate',
                'latitude': -6.8162,
                'longitude': 39.2691,
                'phone': '+255712345002',
                'location': 'Kariakoo, Dar es Salaam',
                'years_of_experience': 10,
                'practice_status': 'active',
                'bar_membership_number': 'TLS-2013-005678',
                'roll_number': 'ADV-005678',
                'office_address': '456 Morogoro Road, Kariakoo',
                'ward': 'Kariakoo',
                'specializations': ['Civil Law', 'Human Rights']
            },
            {
                'email': 'advocate3@pola.test',
                'first_name': 'David',
                'last_name': 'Mbwana',
                'user_type': 'advocate',
                'latitude': -6.7500,
                'longitude': 39.2200,
                'phone': '+255712345003',
                'location': 'Oysterbay, Dar es Salaam',
                'years_of_experience': 12,
                'practice_status': 'active',
                'bar_membership_number': 'TLS-2011-009012',
                'office_address': '789 Toure Drive, Oysterbay',
                'ward': 'Oysterbay',
                'specializations': ['Constitutional Law', 'Administrative Law']
            },
            
            # Lawyers
            {
                'email': 'lawyer1@pola.test',
                'first_name': 'Peter',
                'last_name': 'Moshi',
                'user_type': 'lawyer',
                'latitude': -6.7732,
                'longitude': 39.2680,
                'phone': '+255712345004',
                'location': 'Masaki, Dar es Salaam',
                'years_of_experience': 8,
                'practice_status': 'active',
                'bar_membership_number': 'TLS-2015-012345',
                'office_address': '321 Masaki Peninsula, Masaki',
                'ward': 'Masaki',
                'specializations': ['Corporate Law', 'Commercial Law']
            },
            {
                'email': 'lawyer2@pola.test',
                'first_name': 'Sarah',
                'last_name': 'Mtawa',
                'user_type': 'lawyer',
                'latitude': -6.7850,
                'longitude': 39.2400,
                'phone': '+255712345005',
                'location': 'Upanga, Dar es Salaam',
                'years_of_experience': 6,
                'practice_status': 'active',
                'office_address': '654 United Nations Road, Upanga',
                'ward': 'Upanga West',
                'specializations': ['Employment Law', 'Labour Law']
            },
            {
                'email': 'lawyer3@pola.test',
                'first_name': 'James',
                'last_name': 'Ndege',
                'user_type': 'lawyer',
                'latitude': -6.8300,
                'longitude': 39.2600,
                'phone': '+255712345006',
                'location': 'Chang\'ombe, Dar es Salaam',
                'years_of_experience': 5,
                'practice_status': 'active',
                'office_address': '987 Nyerere Road, Chang\'ombe',
                'ward': 'Chang\'ombe',
                'specializations': ['Contract Law', 'Property Law']
            },
            
            # Paralegals
            {
                'email': 'paralegal1@pola.test',
                'first_name': 'Grace',
                'last_name': 'Hamisi',
                'user_type': 'paralegal',
                'latitude': -6.8235,
                'longitude': 39.2582,
                'phone': '+255712345007',
                'location': 'Temeke, Dar es Salaam',
                'years_of_experience': 4,
                'practice_status': 'active',
                'office_address': '147 Temeke Road, Temeke',
                'ward': 'Temeke',
                'specializations': ['Legal Research', 'Document Preparation']
            },
            {
                'email': 'paralegal2@pola.test',
                'first_name': 'Daniel',
                'last_name': 'Juma',
                'user_type': 'paralegal',
                'latitude': -6.7650,
                'longitude': 39.2850,
                'phone': '+255712345008',
                'location': 'Mikocheni, Dar es Salaam',
                'years_of_experience': 3,
                'practice_status': 'active',
                'office_address': '258 Ali Hassan Mwinyi Road, Mikocheni',
                'ward': 'Mikocheni',
                'specializations': ['Court Filing', 'Client Support']
            },
            
            # Law Firms
            {
                'email': 'lawfirm1@pola.test',
                'first_name': 'Mkono',
                'last_name': 'Associates',
                'user_type': 'law_firm',
                'latitude': -6.7630,
                'longitude': 39.2750,
                'phone': '+255712345009',
                'location': 'Upanga West, Dar es Salaam',
                'years_of_experience': 28,
                'practice_status': 'active',
                'office_address': 'Pamba House, 8th Floor, Kivukoni',
                'ward': 'Kivukoni',
                'firm_name': 'Mkono & Associates',
                'managing_partner': 'Joseph Mkono',
                'number_of_lawyers': 25,
                'year_established': 1995,
                'specializations': ['Commercial Law', 'Tax Law', 'Corporate Law']
            },
            {
                'email': 'lawfirm2@pola.test',
                'first_name': 'Haki',
                'last_name': 'Legal Partners',
                'user_type': 'law_firm',
                'latitude': -6.7900,
                'longitude': 39.2500,
                'phone': '+255712345010',
                'location': 'Kisutu, Dar es Salaam',
                'years_of_experience': 20,
                'practice_status': 'active',
                'office_address': 'Golden Jubilee Towers, 3rd Floor, Kisutu',
                'ward': 'Kisutu',
                'firm_name': 'Haki Legal Partners',
                'managing_partner': 'Sarah Haki',
                'number_of_lawyers': 15,
                'year_established': 2003,
                'specializations': ['Banking Law', 'Finance Law', 'Real Estate']
            },
            {
                'email': 'lawfirm3@pola.test',
                'first_name': 'Sheria',
                'last_name': 'Chambers',
                'user_type': 'law_firm',
                'latitude': -6.8100,
                'longitude': 39.2900,
                'phone': '+255712345011',
                'location': 'Kinondoni, Dar es Salaam',
                'years_of_experience': 15,
                'practice_status': 'active',
                'office_address': 'Azikiwe Street Building, 5th Floor, Kinondoni',
                'ward': 'Kinondoni',
                'firm_name': 'Sheria Chambers',
                'managing_partner': 'Michael Sheria',
                'number_of_lawyers': 12,
                'year_established': 2008,
                'specializations': ['Intellectual Property', 'Technology Law', 'Media Law']
            },
        ]

        # Create test citizen user (rama)
        rama_data = {
            'email': 'rama@pola.test',
            'first_name': 'Rama',
            'last_name': 'Seeker',
            'user_type': 'citizen',
            'latitude': -6.8000,
            'longitude': 39.2500,
            'phone': '+255712345000',
            'location': 'Ilala, Dar es Salaam'
        }

        all_users = [rama_data] + legal_professionals

        created_count = 0
        updated_count = 0
        
        # Get Dar es Salaam region and districts
        dar_region = Region.objects.filter(name__icontains='Dar').first()
        ilala_district = District.objects.filter(name__icontains='Ilala').first() if dar_region else None
        kinondoni_district = District.objects.filter(name__icontains='Kinondoni').first() if dar_region else None
        temeke_district = District.objects.filter(name__icontains='Temeke').first() if dar_region else None

        for data in all_users:
            try:
                # Create or get user
                user, created = User.objects.get_or_create(
                    email=data['email'],
                    defaults={
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'is_active': True,
                        'agreed_to_Terms': True,
                    }
                )

                if created:
                    user.set_password('password123')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Created user: {user.email}'))
                    created_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'- User already exists: {user.email}'))
                    updated_count += 1

                # Get or create UserRole and assign to user
                role, _ = UserRole.objects.get_or_create(
                    role_name=data['user_type']
                )
                user.user_role = role
                
                # Update professional fields for legal professionals (not citizens)
                if data['user_type'] != 'citizen':
                    user.years_of_experience = data.get('years_of_experience')
                    user.practice_status = data.get('practice_status')
                    user.bar_membership_number = data.get('bar_membership_number')
                    user.roll_number = data.get('roll_number')
                    
                    # Law firm specific fields
                    if data['user_type'] == 'law_firm':
                        user.firm_name = data.get('firm_name')
                        # managing_partner is a ForeignKey - would need to be another user, skip for seed data
                        user.number_of_lawyers = data.get('number_of_lawyers')
                        user.year_established = data.get('year_established')
                
                user.save()

                # Create or update contact
                Contact.objects.update_or_create(
                    user=user,
                    defaults={
                        'phone_number': data['phone'],
                    }
                )
                
                # Create or update address for legal professionals
                if data['user_type'] != 'citizen' and data.get('office_address'):
                    # Determine district based on location
                    district = None
                    if 'Temeke' in data['location'] or 'Chang\'ombe' in data['location']:
                        district = temeke_district
                    elif 'Kinondoni' in data['location'] or 'Mikocheni' in data['location'] or 'Masaki' in data['location']:
                        district = kinondoni_district
                    else:
                        district = ilala_district
                    
                    Address.objects.update_or_create(
                        user=user,
                        defaults={
                            'office_address': data.get('office_address'),
                            'ward': data.get('ward'),
                            'district': district,
                            'region': dar_region,
                        }
                    )
                
                # Add specializations for legal professionals
                if data['user_type'] != 'citizen' and data.get('specializations'):
                    # Clear existing specializations
                    ProfessionalSpecialization.objects.filter(user=user).delete()
                    
                    for idx, spec_name in enumerate(data['specializations']):
                        # Get or create specialization
                        specialization, _ = Specialization.objects.get_or_create(
                            name_en=spec_name,
                            defaults={'name_sw': spec_name}
                        )
                        
                        # Create user specialization
                        ProfessionalSpecialization.objects.create(
                            user=user,
                            specialization=specialization,
                            years_of_experience=random.randint(2, user.years_of_experience) if user.years_of_experience else 3,
                            is_primary=(idx == 0)
                        )

                # Create or update device with location
                device_id = f"seed_device_{user.email}"
                device, device_created = UserDevice.objects.update_or_create(
                    user=user,
                    device_id=device_id,
                    defaults={
                        'device_name': f"{data['first_name']}'s Device",
                        'device_type': 'mobile',
                        'os_name': 'android',
                        'latitude': data['latitude'],
                        'longitude': data['longitude'],
                        'is_active': True,
                    }
                )

                if device_created:
                    self.stdout.write(f'  ✓ Created device at ({data["latitude"]}, {data["longitude"]})')
                else:
                    self.stdout.write(f'  ✓ Updated device location')
                
                if data['user_type'] != 'citizen':
                    self.stdout.write(f'  ✓ Added specializations and professional details')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error creating {data["email"]}: {str(e)}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'=== Seeding Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} users'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count} users'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Test login:'))
        self.stdout.write(self.style.SUCCESS('  Email: rama@pola.test'))
        self.stdout.write(self.style.SUCCESS('  Password: password123'))
