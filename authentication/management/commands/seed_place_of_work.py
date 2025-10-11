from django.core.management.base import BaseCommand
from authentication.models import PlaceOfWork

class Command(BaseCommand):
    help = 'Seed place of work data'

    def handle(self, *args, **kwargs):
        # List of place of work options with English and Swahili names
        places_of_work = [
            {
                'code': 'law_firm',
                'en': 'Law Firm',
                'sw': 'Ofisi ya Mawakili'
            },
            {
                'code': 'legal_aid',
                'en': 'Legal Aid Organization',
                'sw': 'Shirika la Usaidizi wa Kisheria'
            },
            {
                'code': 'government',
                'en': 'Government Agency',
                'sw': 'Idara ya Serikali'
            },
            {
                'code': 'private_company',
                'en': 'Private Company',
                'sw': 'Kampuni Binafsi'
            },
            {
                'code': 'ngo',
                'en': 'Non-Governmental Organization (NGO)',
                'sw': 'Shirika Lisilo la Kiserikali'
            },
            {
                'code': 'court',
                'en': 'Court/Judiciary',
                'sw': 'Mahakama'
            },
            {
                'code': 'university',
                'en': 'University/Academic Institution',
                'sw': 'Chuo Kikuu/Taasisi ya Elimu'
            },
            {
                'code': 'international_org',
                'en': 'International Organization',
                'sw': 'Shirika la Kimataifa'
            },
            {
                'code': 'self_employed',
                'en': 'Self-Employed/Independent Practice',
                'sw': 'Kujitegemea/Kazi Huru'
            },
            {
                'code': 'corporate_legal',
                'en': 'Corporate Legal Department',
                'sw': 'Idara ya Kisheria ya Kampuni'
            }
        ]

        for place in places_of_work:
            PlaceOfWork.objects.get_or_create(
                code=place['code'],
                defaults={
                    'name_en': place['en'],
                    'name_sw': place['sw']
                }
            )
            self.stdout.write(f"Created place of work: {place['en']} / {place['sw']}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded place of work data'))
