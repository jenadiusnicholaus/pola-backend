from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import RegionalChapter, Region, PolaUser
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed regional chapters for Tanzania'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting to seed regional chapters...'))
        
        try:
            with transaction.atomic():
                # Get all regions
                regions = Region.objects.all()
                
                if not regions.exists():
                    self.stdout.write(self.style.ERROR('No regions found. Please seed regions first using seed_regions_districts'))
                    return
                
                created_count = 0
                
                for region in regions:
                    # Check if chapter already exists
                    chapter, created = RegionalChapter.objects.get_or_create(
                        region=region,
                        defaults={
                            'name': f'{region.name} Chapter',
                            'description': f'Legal professionals chapter for {region.name} region',
                            'slug': slugify(f'{region.name}-chapter'),
                            'is_active': True,
                            'established_date': '2020-01-01',
                            'contact_email': f'{slugify(region.name)}@pola.co.tz',
                            'phone_number': '+255 123 456 789',
                            'address': f'Pola Chapter Office, {region.name}, Tanzania',
                            'meeting_frequency': 'monthly',
                            'membership_fee': 50000.00,  # TZS 50,000
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created chapter: {chapter.name}'))
                    else:
                        self.stdout.write(self.style.NOTICE(f'  - Chapter already exists: {chapter.name}'))
                
                # Create chapter leadership positions
                self._create_chapter_leadership()
                
                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} regional chapters!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding regional chapters: {str(e)}'))
            raise

    def _create_chapter_leadership(self):
        """Create leadership positions for chapters"""
        chapters = RegionalChapter.objects.all()
        
        # Create or get a superuser to be chapter president
        try:
            superuser = PolaUser.objects.filter(is_superuser=True).first()
            if not superuser:
                self.stdout.write(self.style.WARNING('No superuser found. Chapter leadership will be unassigned.'))
                return
            
            for chapter in chapters:
                # Assign chapter president (using superuser for demo)
                if not chapter.president:
                    chapter.president = superuser
                    chapter.save()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Assigned president for {chapter.name}'))
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not assign chapter leadership: {str(e)}'))
