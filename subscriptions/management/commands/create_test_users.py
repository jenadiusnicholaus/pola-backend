"""
Management command to create role-based test users for Postman testing.
Usage: python manage.py create_test_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import UserRole, Verification
from subscriptions.models import ConsultantProfile
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create role-based test users for Postman'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Creating test users...'))

        # 1. Ensure Roles Exist
        roles_data = [
            {'role_name': 'citizen', 'description': 'Regular citizen user'},
            {'role_name': 'advocate', 'description': 'Licensed Advocate'},
            {'role_name': 'lawyer', 'description': 'Legal Professional / Lawyer'},
            {'role_name': 'paralegal', 'description': 'Paralegal Assistant'},
            {'role_name': 'law_firm', 'description': 'Law Firm Organization'},
        ]

        roles = {}
        for rd in roles_data:
            role, created = UserRole.objects.get_or_create(
                role_name=rd['role_name'],
                defaults={'description': rd['description']}
            )
            roles[rd['role_name']] = role
            if created:
                self.stdout.write(f"Created role: {rd['role_name']}")

        # 2. Test User Data
        password = "testpola2026"
        test_users = [
            {
                'email': 'test_citizen@pola.co.tz',
                'role': 'citizen',
                'first_name': 'Test',
                'last_name': 'Citizen'
            },
            {
                'email': 'test_advocate@pola.co.tz',
                'role': 'advocate',
                'first_name': 'Test',
                'last_name': 'Advocate',
                'roll_number': 'ADV/2024/0001'
            },
            {
                'email': 'test_lawyer@pola.co.tz',
                'role': 'lawyer',
                'first_name': 'Test',
                'last_name': 'Lawyer'
            },
            {
                'email': 'test_paralegal@pola.co.tz',
                'role': 'paralegal',
                'first_name': 'Test',
                'last_name': 'Paralegal'
            },
            {
                'email': 'test_lawfirm@pola.co.tz',
                'role': 'law_firm',
                'first_name': 'Test',
                'last_name': 'LawFirm',
                'firm_name': 'Test Pola Law Firm'
            },
        ]

        for ud in test_users:
            role = roles[ud['role']]
            user, created = User.objects.get_or_create(
                email=ud['email'],
                defaults={
                    'first_name': ud['first_name'],
                    'last_name': ud['last_name'],
                    'user_role': role,
                    'is_active': True,
                    'years_of_experience': 5 if ud['role'] != 'citizen' else 0,
                    'roll_number': ud.get('roll_number') if ud.get('roll_number') else None,
                    'firm_name': ud.get('firm_name', '')
                }
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {ud['email']}"))
            else:
                self.stdout.write(f"User already exists: {ud['email']}")

            # 3. Handle Verification
            verification, v_created = Verification.objects.get_or_create(
                user=user,
                defaults={
                    'status': 'verified',
                    'current_step': 'final'
                }
            )
            if not v_created:
                verification.status = 'verified'
                verification.current_step = 'final'
                verification.save()

            # 4. Create Consultant Profile for Professionals
            if ud['role'] in ['advocate', 'lawyer', 'paralegal', 'law_firm']:
                profile, p_created = ConsultantProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'consultant_type': ud['role'],
                        'specialization': 'General Legal Advice, Civil Law, Criminal Law',
                        'years_of_experience': user.years_of_experience or 5,
                        'offers_mobile_consultations': True,
                        'offers_physical_consultations': True,
                        'city': 'Dar es Salaam',
                        'is_available': True,
                        'average_rating': 4.5
                    }
                )
                if p_created:
                    self.stdout.write(f"Created consultant profile for: {ud['email']}")
                else:
                    # Ensure physical consultations and location are enabled for testing
                    profile.offers_physical_consultations = True
                    profile.city = 'Dar es Salaam'
                    profile.save()

        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('TEST USERS CREATED SUCCESSFULLY'))
        self.stdout.write(self.style.SUCCESS(f"Password for all: {password}"))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        for ud in test_users:
            self.stdout.write(f"{ud['role'].upper():10} | {ud['email']}")
        self.stdout.write(self.style.SUCCESS('=' * 50))
