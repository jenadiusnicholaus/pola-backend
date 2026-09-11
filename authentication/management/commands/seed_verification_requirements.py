from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import UserRole, VerificationRequirement, DocumentType


class Command(BaseCommand):
    help = 'Seed default document types and verification requirements for each professional role'

    def handle(self, *args, **options):
        # Step 1: Seed DocumentType records
        doc_types = [
            {'code': 'roll_number_cert', 'label': 'Roll Number Certificate'},
            {'code': 'practice_license', 'label': 'Practice License'},
            {'code': 'work_certificate', 'label': 'Certificate of Work'},
            {'code': 'professional_cert', 'label': 'Professional Certificate'},
            {'code': 'employment_letter', 'label': 'Employment Letter'},
            {'code': 'organization_cert', 'label': 'Organization Certificate'},
            {'code': 'business_license', 'label': 'Business License'},
            {'code': 'registration_cert', 'label': 'Registration Certificate'},
            {'code': 'firm_documents', 'label': 'Other Firm Documents'},
            {'code': 'id_document', 'label': 'ID Document'},
            {'code': 'academic', 'label': 'Academic Certificate'},
            {'code': 'other', 'label': 'Other Document'},
        ]

        # Step 2: Seed VerificationRequirement records
        requirements = [
            # Advocate
            {'role': 'advocate', 'doc_type_code': 'roll_number_cert', 'label': 'Roll Number Certificate', 'is_required': True, 'sort_order': 1},
            {'role': 'advocate', 'doc_type_code': 'practice_license', 'label': 'Practice License', 'is_required': True, 'sort_order': 2},
            {'role': 'advocate', 'doc_type_code': 'work_certificate', 'label': 'Certificate of Work', 'is_required': False, 'sort_order': 3},

            # Lawyer
            {'role': 'lawyer', 'doc_type_code': 'professional_cert', 'label': 'Professional Certificate', 'is_required': True, 'sort_order': 1},
            {'role': 'lawyer', 'doc_type_code': 'employment_letter', 'label': 'Employment Letter', 'is_required': True, 'sort_order': 2},
            {'role': 'lawyer', 'doc_type_code': 'organization_cert', 'label': 'Organization Certificate', 'is_required': False, 'sort_order': 3},

            # Paralegal
            {'role': 'paralegal', 'doc_type_code': 'professional_cert', 'label': 'Professional Certificate', 'is_required': True, 'sort_order': 1},
            {'role': 'paralegal', 'doc_type_code': 'employment_letter', 'label': 'Employment Letter', 'is_required': True, 'sort_order': 2},
            {'role': 'paralegal', 'doc_type_code': 'organization_cert', 'label': 'Organization Certificate', 'is_required': False, 'sort_order': 3},

            # Law Firm
            {'role': 'law_firm', 'doc_type_code': 'business_license', 'label': 'Business License', 'is_required': True, 'sort_order': 1},
            {'role': 'law_firm', 'doc_type_code': 'registration_cert', 'label': 'Registration Certificate', 'is_required': True, 'sort_order': 2},
            {'role': 'law_firm', 'doc_type_code': 'firm_documents', 'label': 'Other Firm Documents', 'is_required': False, 'sort_order': 3},
        ]

        dt_created = 0
        dt_updated = 0
        vr_created = 0
        vr_updated = 0

        with transaction.atomic():
            # Create/update document types
            for dt in doc_types:
                obj, created = DocumentType.objects.update_or_create(
                    code=dt['code'],
                    defaults={'label': dt['label']}
                )
                if created:
                    dt_created += 1
                else:
                    dt_updated += 1

            # Create/update verification requirements
            for req in requirements:
                role, _ = UserRole.objects.get_or_create(role_name=req['role'])
                doc_type = DocumentType.objects.get(code=req['doc_type_code'])
                obj, created = VerificationRequirement.objects.update_or_create(
                    role=role,
                    document_type_ref=doc_type,
                    defaults={
                        'label': req['label'],
                        'is_required': req['is_required'],
                        'sort_order': req['sort_order'],
                    }
                )
                if created:
                    vr_created += 1
                else:
                    vr_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded document types: {dt_created} created, {dt_updated} updated.\n'
            f'Seeded verification requirements: {vr_created} created, {vr_updated} updated.'
        ))
