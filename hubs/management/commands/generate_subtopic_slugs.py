from django.core.management.base import BaseCommand
from hubs.models import LegalEdSubTopic
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Generate slugs for subtopics that don't have them'

    def handle(self, *args, **options):
        subtopics_without_slug = LegalEdSubTopic.objects.filter(slug__isnull=True) | LegalEdSubTopic.objects.filter(slug='')
        count = subtopics_without_slug.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All subtopics have slugs.'))
            return
        
        self.stdout.write(f'Found {count} subtopics without slugs. Generating...')
        
        for subtopic in subtopics_without_slug:
            base_slug = slugify(subtopic.name)
            slug = base_slug
            counter = 1
            
            # Ensure uniqueness within the same topic
            while LegalEdSubTopic.objects.filter(
                topic=subtopic.topic, 
                slug=slug
            ).exclude(id=subtopic.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            subtopic.slug = slug
            subtopic.save(update_fields=['slug'])
            self.stdout.write(f'  - {subtopic.name} -> {slug}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated slugs for {count} subtopics.'))
