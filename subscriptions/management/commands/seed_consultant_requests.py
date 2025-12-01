"""
Management command to seed consultant registration requests
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from authentication.models import PolaUser
from subscriptions.models import ConsultantRegistrationRequest
import random


class Command(BaseCommand):
    help = 'Seed consultant registration request test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of requests to create'
        )

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        self.stdout.write(f'Seeding {count} consultant registration requests...\n')
        
        # Get users who are advocates, lawyers, or paralegals
        eligible_users = PolaUser.objects.filter(
            user_role__role_name__in=['advocate', 'lawyer', 'paralegal']
        ).exclude(
            id__in=ConsultantRegistrationRequest.objects.values_list('user_id', flat=True)
        ).exclude(
            consultant_profile__isnull=False
        )[:count]

        if not eligible_users.exists():
            self.stdout.write(self.style.WARNING(
                'No eligible users found. Creating test users first...'
            ))
            self._create_test_users(count)
            eligible_users = PolaUser.objects.filter(
                user_role__role_name__in=['advocate', 'lawyer', 'paralegal']
            ).exclude(
                id__in=ConsultantRegistrationRequest.objects.values_list('user_id', flat=True)
            ).exclude(
                consultant_profile__isnull=False
            )[:count]

        consultant_types = ['advocate', 'lawyer', 'paralegal']
        availability_statuses = ['available', 'busy']
        locations = [
            'Dar es Salaam, Tanzania',
            'Arusha, Tanzania',
            'Mwanza, Tanzania',
            'Dodoma, Tanzania',
            'Mbeya, Tanzania',
            'Morogoro, Tanzania',
            'Tanga, Tanzania',
            'Zanzibar, Tanzania',
        ]
        
        bios = [
            "Experienced legal professional with expertise in criminal and civil law. Dedicated to providing quality legal services to clients.",
            "Passionate about justice and client advocacy. Specialized in family law and property disputes.",
            "Corporate lawyer with strong background in contract law and business transactions.",
            "Criminal defense attorney with proven track record in court proceedings.",
            "Legal consultant specializing in employment law and labor disputes.",
            "Advocate with focus on human rights and constitutional law.",
            "Experienced paralegal with extensive knowledge of legal procedures and documentation.",
            "Legal practitioner committed to affordable and accessible legal services.",
        ]

        statuses = ['pending', 'approved', 'rejected']
        status_weights = [0.6, 0.3, 0.1]  # 60% pending, 30% approved, 10% rejected

        created_count = 0
        for user in eligible_users:
            try:
                # Determine consultant type based on user role
                role_name = user.user_role.role_name.lower()
                if role_name in consultant_types:
                    consultant_type = role_name
                else:
                    consultant_type = random.choice(consultant_types)

                # Determine if physical consultation is offered
                offers_physical = consultant_type in ['advocate', 'lawyer'] and random.choice([True, False])
                
                # Create dummy files (in production, these would be real uploads)
                license_content = ContentFile(b'dummy license content', name=f'license_{user.id}.pdf')
                id_content = ContentFile(b'dummy id content', name=f'id_{user.id}.pdf')
                cv_content = ContentFile(b'dummy cv content', name=f'cv_{user.id}.pdf')
                
                # Create request
                request = ConsultantRegistrationRequest.objects.create(
                    user=user,
                    consultant_type=consultant_type,
                    offers_mobile_consultations=True,
                    offers_physical_consultations=offers_physical,
                    preferred_consultation_city=random.choice(locations).split(',')[0] if offers_physical else '',
                    status=random.choices(statuses, weights=status_weights)[0],
                )
                
                request.license_document.save(f'license_{user.id}.pdf', license_content, save=False)
                request.id_document.save(f'id_{user.id}.pdf', id_content, save=False)
                request.cv_document.save(f'cv_{user.id}.pdf', cv_content, save=False)
                request.save()

                # Add admin notes for rejected requests
                if request.status == 'rejected':
                    admin_notes = [
                        "Insufficient documentation provided.",
                        "Professional license is not clear or readable.",
                        "Years of experience do not meet minimum requirements.",
                        "Incomplete information in application.",
                    ]
                    request.admin_notes = random.choice(admin_notes)
                    request.save()

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created {request.status} request for {user.email} ({consultant_type})'
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to create request for {user.email}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} consultant registration requests')
        )

        # Summary
        pending = ConsultantRegistrationRequest.objects.filter(status='pending').count()
        approved = ConsultantRegistrationRequest.objects.filter(status='approved').count()
        rejected = ConsultantRegistrationRequest.objects.filter(status='rejected').count()
        
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Pending:  {pending}')
        self.stdout.write(f'  Approved: {approved}')
        self.stdout.write(f'  Rejected: {rejected}')
        self.stdout.write(f'  Total:    {pending + approved + rejected}\n')

    def _create_test_users(self, count):
        """Create test users if none exist"""
        from authentication.models import UserRole, Region, District, Specialization
        
        self.stdout.write('Creating test users...\n')
        
        # Get or create roles
        advocate_role, _ = UserRole.objects.get_or_create(
            role_name='advocate',
            defaults={'description': 'Licensed Advocate'}
        )
        lawyer_role, _ = UserRole.objects.get_or_create(
            role_name='lawyer',
            defaults={'description': 'Legal Lawyer'}
        )
        paralegal_role, _ = UserRole.objects.get_or_create(
            role_name='paralegal',
            defaults={'description': 'Paralegal Professional'}
        )
        
        roles = [advocate_role, lawyer_role, paralegal_role]
        
        # Get regions and districts
        region = Region.objects.first()
        district = District.objects.first() if region else None
        
        # Get specializations
        specializations = list(Specialization.objects.all()[:3])
        
        for i in range(count):
            role = random.choice(roles)
            email = f'test_{role.role_name}_{i}@example.com'
            
            # Skip if user already exists
            if PolaUser.objects.filter(email=email).exists():
                continue
            
            user = PolaUser.objects.create_user(
                email=email,
                password='testpass123',
                first_name=f'Test{i}',
                last_name=role.role_name.capitalize(),
                user_role=role,
                years_of_experience=random.randint(2, 15),
            )
            
            # Create verification record
            from authentication.models import UserVerification
            UserVerification.objects.create(
                user=user,
                is_verified=True,
                verification_status='verified'
            )
            
            # Add specializations
            if specializations:
                user.specializations.set(random.sample(specializations, min(2, len(specializations))))
            
            # Add roll number for advocates
            if role.role_name == 'advocate':
                user.roll_number = f'ADV/{random.randint(2010, 2024)}/{random.randint(1000, 9999)}'
                user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created test user: {email}'))
