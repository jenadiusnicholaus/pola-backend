"""
Management command to seed bilingual role descriptions into the database.
This ensures all UserRole records have proper English and Swahili descriptions.
"""

from django.core.management.base import BaseCommand
from authentication.models import UserRole


class Command(BaseCommand):
    help = 'Seeds bilingual descriptions for all user roles'

    def handle(self, *args, **options):
        self.stdout.write('Seeding bilingual role descriptions...\n')
        
        updated_count = 0
        created_count = 0
        
        for role_code, data in UserRole.ROLE_CHOICES:
            role, created = UserRole.objects.get_or_create(
                role_name=role_code,
                defaults={
                    'description_en': data.get('description_en', ''),
                    'description_sw': data.get('description_sw', ''),
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Created role: {data["display"]}')
                )
            else:
                # Update existing role with descriptions if not already set
                changed = False
                if not role.description_en and data.get('description_en'):
                    role.description_en = data['description_en']
                    changed = True
                if not role.description_sw and data.get('description_sw'):
                    role.description_sw = data['description_sw']
                    changed = True
                
                if changed:
                    role.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Updated role: {data["display"]}')
                    )
                else:
                    self.stdout.write(f'  Skipped (already has descriptions): {data["display"]}')
        
        self.stdout.write('\n')
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created: {created_count}, Updated: {updated_count}'
        ))
        
        # Display the roles in their correct order
        self.stdout.write('\n--- Roles in Display Order ---')
        self.stdout.write('(Swahili | English format)\n')
        
        for idx, (role_code, data) in enumerate(UserRole.ROLE_CHOICES, 1):
            self.stdout.write(f'{idx}. {data["display"]}')
            self.stdout.write(f'   EN: {data["description_en"][:60]}...')
            self.stdout.write(f'   SW: {data["description_sw"][:60]}...')
            self.stdout.write('')
