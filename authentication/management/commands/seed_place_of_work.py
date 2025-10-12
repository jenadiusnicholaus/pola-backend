from django.core.management.base import BaseCommand
from authentication.models import PlaceOfWork

class Command(BaseCommand):
    help = 'Seed place of work data'

    def handle(self, *args, **kwargs):
        # List of place of work options with English and Swahili names
        places_of_work = [
            {
                'en': 'Law Firm',
                'sw': 'Ofisi ya Mawakili'
            },
            {
                'en': 'Legal Aid Organization',
                'sw': 'Shirika la Usaidizi wa Kisheria'
            },
            {
                'en': 'Government Agency',
                'sw': 'Idara ya Serikali'
            },
            {
                'en': 'Private Company',
                'sw': 'Kampuni Binafsi'
            },
            {
                'en': 'Non-Governmental Organization (NGO)',
                'sw': 'Shirika Lisilo la Kiserikali'
            },
            {
                'en': 'Court/Judiciary',
                'sw': 'Mahakama'
            },
            {
                'en': 'University/Academic Institution',
                'sw': 'Chuo Kikuu/Taasisi ya Elimu'
            },
            {
                'en': 'International Organization',
                'sw': 'Shirika la Kimataifa'
            },
            {
                'en': 'Self-Employed/Independent Practice',
                'sw': 'Kujitegemea/Kazi Huru'
            },
            {
                'en': 'Corporate Legal Department',
                'sw': 'Idara ya Kisheria ya Kampuni'
            }
        ]

        for place in places_of_work:
            obj, created = PlaceOfWork.objects.get_or_create(
                name_en=place['en'],
                defaults={
                    'name_sw': place['sw']
                }
            )
            if created:
                self.stdout.write(f"Created place of work: {place['en']} / {place['sw']} (code: {obj.code})")
            else:
                self.stdout.write(f"Place of work already exists: {place['en']} / {place['sw']} (code: {obj.code})")

        self.stdout.write(self.style.SUCCESS('Successfully seeded place of work data'))
