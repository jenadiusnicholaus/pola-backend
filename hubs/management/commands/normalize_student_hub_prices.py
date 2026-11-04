from decimal import Decimal

from django.core.management.base import BaseCommand

from documents.models import LearningMaterial

DOWNLOADABLE_PRICE = Decimal('1500.00')
FREE_PRICE = Decimal('0.00')


class Command(BaseCommand):
    help = (
        'Normalize Students Hub prices: downloadable content costs a fixed '
        'TZS 1,500 and non-downloadable content is free.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would change without updating anything',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        downloadable_qs = LearningMaterial.objects.filter(
            hub_type='students',
            is_downloadable=True,
        ).exclude(price=DOWNLOADABLE_PRICE)

        non_downloadable_qs = LearningMaterial.objects.filter(
            hub_type='students',
            is_downloadable=False,
        ).exclude(price=FREE_PRICE)

        self.stdout.write(
            f'Downloadable students-hub items to set to {DOWNLOADABLE_PRICE}: '
            f'{downloadable_qs.count()}'
        )
        self.stdout.write(
            f'Non-downloadable students-hub items to set to {FREE_PRICE}: '
            f'{non_downloadable_qs.count()}'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run - no changes made'))
            return

        updated_paid = downloadable_qs.update(price=DOWNLOADABLE_PRICE)
        updated_free = non_downloadable_qs.update(price=FREE_PRICE)

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated_paid} downloadable and {updated_free} '
                f'non-downloadable students-hub items'
            )
        )
