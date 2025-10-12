from django.core.management.base import BaseCommand
from authentication.models import UserRole

class Command(BaseCommand):
    help = 'Seed user roles data'

    def handle(self, *args, **kwargs):
        # List of user roles
        roles = [
            {
                'role_name': 'lawyer',
                'description': 'Legal professional working in various organizations'
            },
            {
                'role_name': 'advocate',
                'description': 'Licensed legal practitioner with roll number'
            },
            {
                'role_name': 'paralegal',
                'description': 'Legal assistant providing support to lawyers and advocates'
            },
            {
                'role_name': 'law_student',
                'description': 'Student studying law at a university'
            },
            {
                'role_name': 'law_firm',
                'description': 'Legal practice organization'
            },
            {
                'role_name': 'citizen',
                'description': 'General public user seeking legal information or services'
            },
        ]

        for role_data in roles:
            role, created = UserRole.objects.get_or_create(
                role_name=role_data['role_name'],
                defaults={'description': role_data['description']}
            )
            if created:
                self.stdout.write(f"Created role: {role.get_role_display()}")
            else:
                self.stdout.write(f"Role already exists: {role.get_role_display()}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded user roles'))
