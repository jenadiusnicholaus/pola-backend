"""
Management command to seed hub posts with diverse content types
Creates test posts with images, files, and YouTube videos across all hubs
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from faker import Faker
import random
from io import BytesIO
from PIL import Image
import requests
from datetime import datetime, timedelta
import pytz

from authentication.models import PolaUser, UserRole
from documents.models import LearningMaterial
from hubs.models import LegalEdTopic, LegalEdSubTopic


class Command(BaseCommand):
    help = 'Seed hub posts with diverse content (images, files, YouTube videos)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of posts to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test posts before seeding'
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']
        
        if options['clear']:
            self.stdout.write('Clearing existing test posts...')
            LearningMaterial.objects.filter(title__startswith='[TEST]').delete()
            self.stdout.write(self.style.SUCCESS('✅ Cleared existing test posts'))

        self.stdout.write(f'Seeding {count} hub posts with diverse content...')
        
        # Get users for different roles
        users = self.get_users_by_role()
        topics = list(LegalEdTopic.objects.all())
        
        # Content templates for different hubs
        content_templates = self.get_content_templates()
        
        # YouTube video links for testing
        youtube_links = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=3JZ_D3ELwOQ',
            'https://www.youtube.com/watch?v=ScMzIvxBSi4',
            'https://www.youtube.com/watch?v=y6120QOlsfU',
            'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
            'https://www.youtube.com/watch?v=ZZ5LpwO-An4',
            'https://www.youtube.com/watch?v=hFZFjoX2cGg',
            'https://www.youtube.com/watch?v=OQQmJAKZLX8'
        ]
        
        created_count = 0
        
        for i in range(count):
            try:
                # Random hub type
                hub_type = random.choice(['advocates', 'students', 'forum', 'legal_ed'])
                
                # Get appropriate user for hub type
                uploader = self.get_random_user_for_hub(users, hub_type)
                if not uploader:
                    continue
                
                # Random content type
                content_type = self.get_random_content_type(hub_type)
                
                # Create base post data
                post_data = {
                    'title': f'[TEST] {self.generate_title(hub_type, content_type, fake)}',
                    'description': self.generate_description(hub_type, content_type, fake),
                    'content': self.generate_content(hub_type, content_type, fake, content_templates),
                    'hub_type': hub_type,
                    'content_type': content_type,
                    'uploader': uploader,
                    'uploader_type': self.get_uploader_type(uploader),
                    'is_active': True,
                    'is_approved': True,
                    'views_count': random.randint(0, 1000),
                    'downloads_count': random.randint(0, 100),
                    'created_at': fake.date_time_between(start_date='-30d', end_date='now', tzinfo=pytz.UTC)
                }
                
                # Add topic for legal_ed hub
                if hub_type == 'legal_ed' and topics:
                    post_data['topic'] = random.choice(topics)
                    if post_data['topic'].subtopics.exists():
                        post_data['subtopic'] = random.choice(list(post_data['topic'].subtopics.all()))
                
                # Add price for some students hub content
                if hub_type == 'students' and random.choice([True, False, False]):  # 33% chance
                    post_data['price'] = random.choice([0, 500, 1000, 1500, 2000, 2500])
                
                # Add video link (YouTube)
                if random.choice([True, False, False]):  # 33% chance
                    post_data['video_url'] = random.choice(youtube_links)
                
                # Create the post
                post = LearningMaterial.objects.create(**post_data)
                
                # Add file attachment
                if random.choice([True, False]):  # 50% chance
                    self.add_file_attachment(post, content_type)
                
                # Add image
                if random.choice([True, False]):  # 50% chance
                    self.add_image_attachment(post, content_type)
                
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f'Created {created_count}/{count} posts...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to create post {i+1}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully created {created_count} test posts across all hubs!')
        )
        
        # Show summary
        self.show_summary()

    def get_users_by_role(self):
        """Get users organized by role"""
        return {
            'advocates': list(PolaUser.objects.filter(user_role__role_name='advocate')),
            'lawyers': list(PolaUser.objects.filter(user_role__role_name='lawyer')),
            'students': list(PolaUser.objects.filter(user_role__role_name='law_student')),
            'lecturers': list(PolaUser.objects.filter(user_role__role_name='lecturer')),
            'admins': list(PolaUser.objects.filter(is_staff=True)),
            'citizens': list(PolaUser.objects.filter(user_role__role_name='citizen')),
            'all': list(PolaUser.objects.all()[:20])  # Limit for performance
        }
    
    def get_random_user_for_hub(self, users, hub_type):
        """Get appropriate user for hub type"""
        if hub_type == 'advocates':
            return random.choice(users['advocates'] + users['admins']) if users['advocates'] or users['admins'] else None
        elif hub_type == 'students':
            return random.choice(users['students'] + users['lecturers'] + users['admins']) if users['students'] or users['lecturers'] or users['admins'] else None
        elif hub_type == 'forum':
            return random.choice(users['all']) if users['all'] else None
        elif hub_type == 'legal_ed':
            return random.choice(users['admins'] + users['lecturers']) if users['admins'] or users['lecturers'] else None
        
        return random.choice(users['all']) if users['all'] else None
    
    def get_uploader_type(self, user):
        """Get uploader type based on user role"""
        if not user.user_role:
            return 'admin' if user.is_staff else 'student'
        
        role_mapping = {
            'advocate': 'advocate',
            'lawyer': 'advocate',
            'law_student': 'student',
            'lecturer': 'lecturer',
            'citizen': 'student'
        }
        
        return role_mapping.get(user.user_role.role_name, 'student')
    
    def get_random_content_type(self, hub_type):
        """Get random content type for hub"""
        content_types = {
            'advocates': ['discussion', 'article', 'news', 'case_study', 'legal_update'],
            'students': ['notes', 'past_papers', 'assignment', 'discussion', 'question', 'tutorial'],
            'forum': ['discussion', 'question', 'news', 'general'],
            'legal_ed': ['lecture', 'article', 'tutorial', 'case_study', 'legal_update']
        }
        
        return random.choice(content_types.get(hub_type, ['discussion']))
    
    def generate_title(self, hub_type, content_type, fake):
        """Generate contextual title"""
        titles = {
            'advocates': {
                'discussion': f"Legal Discussion: {fake.catch_phrase()}",
                'article': f"Legal Analysis: {fake.bs().title()}",
                'news': f"Legal News: {fake.company()} Case Update",
                'case_study': f"Case Study: {fake.company()} vs {fake.company()}",
                'legal_update': f"Legal Update: {fake.catch_phrase()}"
            },
            'students': {
                'notes': f"Study Notes: {fake.job()} Law",
                'past_papers': f"Past Paper: {fake.year()} {fake.job()} Exam",
                'assignment': f"Assignment: {fake.catch_phrase()}",
                'discussion': f"Student Discussion: {fake.sentence(nb_words=4)}",
                'question': f"Question: {fake.sentence(nb_words=6)}?",
                'tutorial': f"Tutorial: {fake.catch_phrase()}"
            },
            'forum': {
                'discussion': f"Community Discussion: {fake.catch_phrase()}",
                'question': f"Help Needed: {fake.sentence(nb_words=5)}?",
                'news': f"Community News: {fake.bs().title()}",
                'general': f"General: {fake.catch_phrase()}"
            },
            'legal_ed': {
                'lecture': f"Lecture: {fake.job()} Law Fundamentals",
                'article': f"Educational Article: {fake.bs().title()}",
                'tutorial': f"Tutorial: {fake.catch_phrase()}",
                'case_study': f"Educational Case: {fake.company()} Analysis",
                'legal_update': f"Legal Education: {fake.catch_phrase()}"
            }
        }
        
        return titles.get(hub_type, {}).get(content_type, fake.sentence(nb_words=4).title())
    
    def generate_description(self, hub_type, content_type, fake):
        """Generate contextual description"""
        descriptions = {
            'advocates': f"Professional legal content for advocates. {fake.paragraph(nb_sentences=2)}",
            'students': f"Educational content for law students. {fake.paragraph(nb_sentences=2)}",
            'forum': f"Community discussion topic. {fake.paragraph(nb_sentences=2)}",
            'legal_ed': f"Legal education resource. {fake.paragraph(nb_sentences=2)}"
        }
        
        return descriptions.get(hub_type, fake.paragraph(nb_sentences=2))
    
    def generate_content(self, hub_type, content_type, fake, templates):
        """Generate rich content with formatting"""
        base_content = fake.paragraph(nb_sentences=5)
        
        # Add contextual content based on type
        if content_type in ['article', 'tutorial', 'lecture']:
            content = f"""
# Introduction

{fake.paragraph(nb_sentences=3)}

## Key Points

1. **{fake.catch_phrase()}**: {fake.paragraph(nb_sentences=2)}
2. **{fake.catch_phrase()}**: {fake.paragraph(nb_sentences=2)}
3. **{fake.catch_phrase()}**: {fake.paragraph(nb_sentences=2)}

## Conclusion

{fake.paragraph(nb_sentences=2)}

---
*Generated for testing purposes*
            """.strip()
        elif content_type == 'case_study':
            content = f"""
# Case Overview

**Case**: {fake.company()} vs {fake.company()}
**Date**: {fake.date()}
**Court**: {fake.city()} High Court

## Facts

{fake.paragraph(nb_sentences=4)}

## Legal Issues

1. {fake.sentence()}
2. {fake.sentence()}
3. {fake.sentence()}

## Decision

{fake.paragraph(nb_sentences=3)}

## Significance

{fake.paragraph(nb_sentences=2)}
            """.strip()
        elif content_type == 'question':
            content = f"""
## Question

{fake.paragraph(nb_sentences=2)}

### Additional Context

{fake.paragraph(nb_sentences=3)}

**Looking for**: {fake.sentence()}
            """.strip()
        else:
            content = f"""
{fake.paragraph(nb_sentences=4)}

### Details

{fake.paragraph(nb_sentences=3)}

### Additional Information

- {fake.sentence()}
- {fake.sentence()}
- {fake.sentence()}

{fake.paragraph(nb_sentences=2)}
            """.strip()
        
        return content
    
    def get_content_templates(self):
        """Get content templates for different types"""
        return {
            'legal_case': """
# Case Analysis: {title}

## Background
{background}

## Legal Principles
{principles}

## Conclusion
{conclusion}
            """,
            'tutorial': """
# Tutorial: {title}

## Learning Objectives
{objectives}

## Content
{content}

## Practice Questions
{questions}
            """,
            'discussion': """
# Discussion: {title}

## Overview
{overview}

## Key Points for Discussion
{points}

## Your Thoughts?
{conclusion}
            """
        }
    
    def add_file_attachment(self, post, content_type):
        """Add file attachment to post"""
        try:
            # Create fake file content
            file_types = {
                'notes': ('pdf', b'%PDF-1.4 fake pdf content'),
                'past_papers': ('pdf', b'%PDF-1.4 fake exam paper'),
                'assignment': ('docx', b'fake docx content'),
                'article': ('pdf', b'%PDF-1.4 fake article'),
                'tutorial': ('pdf', b'%PDF-1.4 fake tutorial'),
                'case_study': ('pdf', b'%PDF-1.4 fake case study'),
                'legal_update': ('pdf', b'%PDF-1.4 fake legal update')
            }
            
            file_ext, file_content = file_types.get(content_type, ('pdf', b'%PDF-1.4 fake content'))
            
            # Create and save file
            file_name = f"test_{content_type}_{random.randint(1000, 9999)}.{file_ext}"
            file_obj = ContentFile(file_content, name=file_name)
            
            post.file = file_obj
            post.save()
            
        except Exception as e:
            self.stdout.write(f"Failed to add file to post {post.id}: {str(e)}")
    
    def add_image_attachment(self, post, content_type):
        """Add image attachment to post"""
        try:
            # Create a simple colored image
            colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
            color = random.choice(colors)
            
            # Create image
            img = Image.new('RGB', (400, 300), color)
            
            # Save to BytesIO
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            
            # Create file (save to file field since cover_image doesn't exist)
            file_name = f"test_image_{content_type}_{random.randint(1000, 9999)}.jpg"
            image_file = ContentFile(img_io.getvalue(), name=file_name)
            
            # Use file field for images too
            if not post.file:
                post.file = image_file
                post.save()
            
        except Exception as e:
            self.stdout.write(f"Failed to add image to post {post.id}: {str(e)}")
    
    def show_summary(self):
        """Show summary of created posts"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SEEDING SUMMARY'))
        self.stdout.write('='*50)
        
        # Count by hub type
        for hub_type in ['advocates', 'students', 'forum', 'legal_ed']:
            count = LearningMaterial.objects.filter(
                title__startswith='[TEST]',
                hub_type=hub_type
            ).count()
            self.stdout.write(f"{hub_type.upper()} Hub: {count} posts")
        
        # Count by content features
        test_posts = LearningMaterial.objects.filter(title__startswith='[TEST]')
        
        with_files = test_posts.exclude(file='').count()
        with_videos = test_posts.exclude(video_url='').count()
        
        self.stdout.write(f"\nContent Features:")
        self.stdout.write(f"Posts with files: {with_files}")
        self.stdout.write(f"Posts with videos: {with_videos}")
        
        self.stdout.write('\n' + self.style.SUCCESS('✅ Seeding completed successfully!'))
        self.stdout.write('\nUse --clear flag to remove test posts before running again.')