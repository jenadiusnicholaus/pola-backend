from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import UserRole, VerificationRequirement


class Command(BaseCommand):
    help = 'Seed default verification requirements for each professional role'

    def handle(self, *args, **options):
        requirements = [
            # Advocate
            {'role': 'advocate', 'document_type': 'roll_number_cert', 'label': 'Roll Number Certificate', 'is_required': True, 'sort_order': 1},
            {'role': 'advocate', 'document_type': 'practice_license', 'label': 'Practice License', 'is_required': True, 'sort_order': 2},
            {'role': 'advocate', 'document_type': 'work_certificate', 'label': 'Certificate of Work', 'is_required': False, 'sort_order': 3},

            # Lawyer
            {'role': 'lawyer', 'document_type': 'professional_cert', 'label': 'Professional Certificate', 'is_required': True, 'sort_order': 1},
            {'role': 'lawyer', 'document_type': 'employment_letter', 'label': 'Employment Letter', 'is_required': True, 'sort_order': 2},
            {'role': 'lawyer', 'document_type': 'organization_cert', 'label': 'Organization Certificate', 'is_required': False, 'sort_order': 3},

            # Paralegal
            {'role': 'paralegal', 'document_type': 'professional_cert', 'label': 'Professional Certificate', 'is_required': True, 'sort_order': 1},
            {'role': 'paralegal', 'document_type': 'employment_letter', 'label': 'Employment Letter', 'is_required': True, 'sort_order': 2},
            {'role': 'paralegal', 'document_type': 'organization_cert', 'label': 'Organization Certificate', 'is_required': False, 'sort_order': 3},

            # Law Firm
            {'role': 'law_firm', 'document_type': 'business_license', 'label': 'Business License', 'is_required': True, 'sort_order': 1},
            {'role': 'law_firm', 'document_type': 'registration_cert', 'label': 'Registration Certificate', 'is_required': True, 'sort_order': 2},
            {'role': 'law_firm', 'document_type': 'firm_documents', 'label': 'Other Firm Documents', 'is_required': False, 'sort_order': 3},
        ]

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for req in requirements:
                role, _ = UserRole.objects.get_or_create(role_name=req['role'])
                obj, created = VerificationRequirement.objects.update_or_create(
                    role=role,
                    document_type=req['document_type'],
                    defaults={
                        'label': req['label'],
                        'is_required': req['is_required'],
                        'sort_order': req['sort_order'],
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded verification requirements: {created_count} created, {updated_count} updated.'
        ))
