from django.core.management.base import BaseCommand
from hubs.models import LegalEdTopic
from documents.models import LearningMaterial


class Command(BaseCommand):
    help = 'Debug topic materials - check topic slugs and material counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic-slug',
            type=str,
            help='Specific topic slug to check'
        )
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='List all topics with material counts'
        )

    def handle(self, *args, **options):
        topic_slug = options.get('topic_slug')
        list_all = options.get('list_all')

        if list_all:
            self.stdout.write(self.style.SUCCESS('=== All Topics with Material Counts ==='))
            topics = LegalEdTopic.objects.all()
            for topic in topics:
                material_count = LearningMaterial.objects.filter(topic=topic).count()
                self.stdout.write(
                    f'ID: {topic.id}, Slug: "{topic.slug}", Name: "{topic.name}", Materials: {material_count}'
                )

        if topic_slug:
            self.stdout.write(self.style.SUCCESS(f'=== Checking Topic: {topic_slug} ==='))
            
            topic = LegalEdTopic.objects.filter(slug=topic_slug).first()
            if topic:
                self.stdout.write(self.style.SUCCESS(f'Topic exists: {topic.name}'))
                self.stdout.write(self.style.SUCCESS(f'Topic ID: {topic.id}'))
                
                materials = LearningMaterial.objects.filter(topic=topic)
                material_count = materials.count()
                self.stdout.write(self.style.SUCCESS(f'Materials count: {material_count}'))
                
                if material_count > 0:
                    self.stdout.write(self.style.SUCCESS('Recent materials:'))
                    for material in materials[:5]:
                        self.stdout.write(
                            f'  - {material.title[:50]}... (ID: {material.id}, Lang: {material.language or "N/A"})'
                        )
                else:
                    self.stdout.write(self.style.WARNING('No materials found for this topic'))
            else:
                self.stdout.write(self.style.ERROR(f'Topic "{topic_slug}" not found'))
                
                # Show available slugs
                available_slugs = LegalEdTopic.objects.values_list('slug', flat=True)
                if available_slugs:
                    self.stdout.write(self.style.SUCCESS('Available topic slugs:'))
                    for slug in available_slugs:
                        self.stdout.write(f'  - "{slug}"')
                else:
                    self.stdout.write(self.style.WARNING('No topics found in database'))

        if not topic_slug and not list_all:
            self.stdout.write(self.style.WARNING('Please specify --topic-slug or --list-all'))
            self.stdout.write('Examples:')
            self.stdout.write('  python manage.py debug_topic_materials --topic-slug=criminal-law')
            self.stdout.write('  python manage.py debug_topic_materials --list-all')
