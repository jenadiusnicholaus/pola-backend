import re
from django.core.management.base import BaseCommand
from authentication.models import PlaceOfWork


def generate_code(name):
    """Generate a URL-safe code from the English name"""
    # Convert to lowercase, replace spaces and special chars with underscores
    code = re.sub(r'[^a-zA-Z0-9]+', '_', name.lower())
    # Remove leading/trailing underscores
    code = code.strip('_')
    return code


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
                'code': 'legal_aid_org',
                'en': 'Legal Aid Organization',
                'sw': 'Shirika la Usaidizi wa Kisheria'
            },
            {
                'code': 'government_agency',
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
                'code': 'court_judiciary',
                'en': 'Court/Judiciary',
                'sw': 'Mahakama'
            },
            {
                'code': 'university_academic',
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
            obj, created = PlaceOfWork.objects.update_or_create(
                code=place['code'],
                defaults={
                    'name_en': place['en'],
                    'name_sw': place['sw']
                }
            )
            if created:
                self.stdout.write(f"Created place of work: {place['en']} / {place['sw']} (code: {obj.code})")
            else:
                self.stdout.write(f"Place of work already exists: {place['en']} / {place['sw']} (code: {obj.code})")

        self.stdout.write(self.style.SUCCESS('Successfully seeded place of work data'))
