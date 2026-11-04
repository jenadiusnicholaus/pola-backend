from django.core.management.base import BaseCommand
from authentication.models import Specialization

class Command(BaseCommand):
    help = 'Seed initial specializations/practice areas'

    def handle(self, *args, **kwargs):
        # List of specializations with English and Swahili names
        specializations = [
            {
                'en': 'Corporate Law',
                'sw': 'Sheria za Kampuni',
                'description': 'Legal practice focusing on business and corporate matters'
            },
            {
                'en': 'Criminal Law',
                'sw': 'Sheria za Jinai',
                'description': 'Legal practice focusing on criminal cases and defense'
            },
            {
                'en': 'Family Law',
                'sw': 'Sheria za Familia',
                'description': 'Legal practice focusing on family matters, divorce, and child custody'
            },
            {
                'en': 'Constitutional Law',
                'sw': 'Sheria za Katiba',
                'description': 'Legal practice focusing on constitutional rights and governance'
            },
            {
                'en': 'Real Estate Law',
                'sw': 'Sheria za Mali Isiyohamishika',
                'description': 'Legal practice focusing on property and real estate matters'
            },
            {
                'en': 'Labour and Employment Law',
                'sw': 'Sheria za Kazi na Ajira',
                'description': 'Legal practice focusing on employment and labour relations'
            },
            {
                'en': 'Tax Law',
                'sw': 'Sheria za Kodi',
                'description': 'Legal practice focusing on taxation and revenue matters'
            },
            {
                'en': 'Intellectual Property',
                'sw': 'Mali ya Kiakili',
                'description': 'Legal practice focusing on patents, trademarks, and copyrights'
            },
            {
                'en': 'Human Rights Law',
                'sw': 'Sheria za Haki za Binadamu',
                'description': 'Legal practice focusing on human rights and civil liberties'
            },
            {
                'en': 'Environmental Law',
                'sw': 'Sheria za Mazingira',
                'description': 'Legal practice focusing on environmental protection and regulations'
            },
            {
                'en': 'Administrative Law',
                'sw': 'Sheria za Utawala',
                'description': 'Legal practice focusing on government administration and regulatory matters'
            },
            {
                'en': 'Contract Law',
                'sw': 'Sheria za Mikataba',
                'description': 'Legal practice focusing on drafting, interpreting, and enforcing contracts'
            },
            {
                'en': 'Civil Litigation',
                'sw': 'Mashauri ya Madai',
                'description': 'Legal practice focusing on representing clients in civil disputes and lawsuits'
            },
            {
                'en': 'Probate Law',
                'sw': 'Sheria za Mirathi',
                'description': 'Legal practice focusing on estates, wills, and inheritance matters'
            },
            {
                'en': 'Banking and Finance Law',
                'sw': 'Sheria za Benki na Fedha',
                'description': 'Legal practice focusing on banking, finance, and financial services regulation'
            },
            {
                'en': 'Insurance Law',
                'sw': 'Sheria za Bima',
                'description': 'Legal practice focusing on insurance policies, claims, and regulation'
            },
            {
                'en': 'Mining and Natural Resources Law',
                'sw': 'Sheria za Madini na Maliasili',
                'description': 'Legal practice focusing on mining, natural resources, and extractive industries'
            },
            {
                'en': 'Cyber Law',
                'sw': 'Sheria za Mtandao',
                'description': 'Legal practice focusing on internet, digital, and information technology matters'
            },
            {
                'en': 'International Law',
                'sw': 'Sheria za Kimataifa',
                'description': 'Legal practice focusing on treaties, cross-border matters, and international relations'
            }
        ]

        for spec in specializations:
            Specialization.objects.get_or_create(
                name_en=spec['en'],
                defaults={
                    'name_sw': spec['sw'],
                    'description': spec['description']
                }
            )
            self.stdout.write(f"Created specialization: {spec['en']} / {spec['sw']}")

        self.stdout.write(self.style.SUCCESS('Successfully seeded specializations'))
