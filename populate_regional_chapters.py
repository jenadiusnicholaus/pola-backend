"""
Populate Regional Chapters for TLS (Tanganyika Law Society)
Run this script to create the initial regional chapters in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.models import RegionalChapter, Region


def populate_chapters():
    """Populate regional chapters for TLS"""
    
    print("=" * 60)
    print("  Populating TLS Regional Chapters")
    print("=" * 60)
    
    chapters_data = [
        ('Dar es Salaam Chapter', 'DSM', 'Dar es Salaam', 'TLS Regional Chapter for Dar es Salaam and surrounding areas'),
        ('Arusha Chapter', 'ARU', 'Arusha', 'TLS Regional Chapter for Arusha and Northern Zone'),
        ('Mwanza Chapter', 'MWZ', 'Mwanza', 'TLS Regional Chapter for Mwanza and Lake Zone'),
        ('Dodoma Chapter', 'DOD', 'Dodoma', 'TLS Regional Chapter for Dodoma (Capital City)'),
        ('Mbeya Chapter', 'MBY', 'Mbeya', 'TLS Regional Chapter for Mbeya and Southern Highlands'),
        ('Moshi Chapter', 'MOS', 'Kilimanjaro', 'TLS Regional Chapter for Moshi/Kilimanjaro Region'),
        ('Tanga Chapter', 'TNG', 'Tanga', 'TLS Regional Chapter for Tanga Region'),
        ('Morogoro Chapter', 'MRG', 'Morogoro', 'TLS Regional Chapter for Morogoro Region'),
        ('Mtwara Chapter', 'MTW', 'Mtwara', 'TLS Regional Chapter for Mtwara and Southern Zone'),
        ('Iringa Chapter', 'IRI', 'Iringa', 'TLS Regional Chapter for Iringa Region'),
        ('Shinyanga Chapter', 'SHI', 'Shinyanga', 'TLS Regional Chapter for Shinyanga Region'),
        ('Tabora Chapter', 'TAB', 'Tabora', 'TLS Regional Chapter for Tabora Region'),
        ('Singida Chapter', 'SIN', 'Singida', 'TLS Regional Chapter for Singida Region'),
    ]
    
    created_count = 0
    existing_count = 0
    
    for name, code, region_name, description in chapters_data:
        # Get or create the region first
        region, region_created = Region.objects.get_or_create(name=region_name)
        if region_created:
            print(f"  📍 Created Region: {region_name}")
        
        # Create or get the chapter
        chapter, created = RegionalChapter.objects.get_or_create(
            name=name,
            defaults={
                'code': code,
                'region': region,
                'description': description,
                'is_active': True
            }
        )
        
        if created:
            created_count += 1
            print(f"  ✅ Created: {name} ({code}) - {region_name}")
        else:
            existing_count += 1
            print(f"  ℹ️  Already exists: {name} ({code})")
    
    print("\n" + "=" * 60)
    print(f"  Summary:")
    print(f"  - New chapters created: {created_count}")
    print(f"  - Existing chapters: {existing_count}")
    print(f"  - Total chapters: {RegionalChapter.objects.count()}")
    print(f"  - Active chapters: {RegionalChapter.objects.filter(is_active=True).count()}")
    print("=" * 60)
    print("✅ Regional Chapters populated successfully!")
    print()


if __name__ == '__main__':
    populate_chapters()
