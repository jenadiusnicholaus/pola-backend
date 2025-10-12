from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Seed all initial data (regions, districts, specializations, place_of_work)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting to seed all data...'))
        
        # Seed user roles
        self.stdout.write(self.style.NOTICE('\n1. Seeding user roles...'))
        call_command('seed_user_roles')
        
        # Seed regions and districts
        self.stdout.write(self.style.NOTICE('\n2. Seeding regions and districts...'))
        call_command('seed_regions_districts')
        
        # Seed specializations
        self.stdout.write(self.style.NOTICE('\n3. Seeding specializations...'))
        call_command('seed_specializations')
        
        # Seed place of work
        self.stdout.write(self.style.NOTICE('\n4. Seeding place of work...'))
        call_command('seed_place_of_work')
        
        self.stdout.write(self.style.SUCCESS('\n✓ All data seeded successfully!'))
