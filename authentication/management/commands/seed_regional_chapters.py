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
                            'description': f'Legal professionals chapter for {region.name} region. Advocates in this region can register and operate under this TLS chapter.',
                            'code': region.code[:3].upper() if region.code else None,
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created chapter: {chapter.name}'))
                    else:
                        self.stdout.write(self.style.NOTICE(f'  - Chapter already exists: {chapter.name}'))
                
                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} regional chapters!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding regional chapters: {str(e)}'))
            raise
