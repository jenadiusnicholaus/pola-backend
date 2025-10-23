"""
Django management command to seed comments and likes for all content

Usage:
    python manage.py seed_engagement
    python manage.py seed_engagement --comments=5 --likes=10
    python manage.py seed_engagement --hub-type=students
    python manage.py seed_engagement --clear
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from documents.models import LearningMaterial
from hubs.models import HubComment, ContentLike, ContentBookmark
from django.db import transaction
import random
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seed comments, likes, and bookmarks for content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--comments',
            type=int,
            default=5,
            help='Number of comments per content (default: 5)'
        )
        parser.add_argument(
            '--likes',
            type=int,
            default=10,
            help='Number of likes per content (default: 10)'
        )
        parser.add_argument(
            '--bookmarks',
            type=int,
            default=3,
            help='Number of bookmarks per content (default: 3)'
        )
        parser.add_argument(
            '--hub-type',
            type=str,
            default=None,
            help='Filter by hub type (advocates, students, forum, legal_ed)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing engagement data before seeding'
        )
        parser.add_argument(
            '--create-users',
            type=int,
            default=0,
            help='Create N fake users for engagement (default: 0)'
        )

    def handle(self, *args, **options):
        comments_per_content = options['comments']
        likes_per_content = options['likes']
        bookmarks_per_content = options['bookmarks']
        hub_type = options['hub_type']
        clear = options['clear']
        create_users_count = options['create_users']

        self.stdout.write(self.style.SUCCESS('\n🌱 Starting engagement seeding...\n'))

        # Create fake users if requested
        if create_users_count > 0:
            self.stdout.write(f'Creating {create_users_count} fake users...')
            created_users = self.create_fake_users(create_users_count)
            self.stdout.write(self.style.SUCCESS(f'✅ Created {len(created_users)} users\n'))

        # Clear existing data if requested
        if clear:
            self.stdout.write(self.style.WARNING('⚠️  Clearing existing engagement data...'))
            with transaction.atomic():
                comments_deleted = HubComment.objects.all().delete()[0]
                likes_deleted = ContentLike.objects.all().delete()[0]
                bookmarks_deleted = ContentBookmark.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(
                f'✅ Deleted {comments_deleted} comments, {likes_deleted} likes, {bookmarks_deleted} bookmarks\n'
            ))

        # Get content queryset
        queryset = LearningMaterial.objects.all()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        content_count = queryset.count()
        
        if content_count == 0:
            self.stdout.write(self.style.ERROR('❌ No content found to seed!'))
            return

        self.stdout.write(f'Found {content_count} content items to seed\n')

        # Get active users for engagement
        users = list(User.objects.filter(is_active=True))
        if len(users) < 3:
            self.stdout.write(self.style.ERROR(
                '❌ Need at least 3 active users. Create users with --create-users=10'
            ))
            return

        self.stdout.write(f'Using {len(users)} active users for engagement\n')

        # Seed engagement
        total_comments = 0
        total_likes = 0
        total_bookmarks = 0

        with transaction.atomic():
            for idx, content in enumerate(queryset, 1):
                self.stdout.write(f'[{idx}/{content_count}] Seeding: {content.title or content.id}')
                
                # Seed comments
                comments_created = self.seed_comments(content, users, comments_per_content)
                total_comments += comments_created
                
                # Seed likes
                likes_created = self.seed_likes(content, users, likes_per_content)
                total_likes += likes_created
                
                # Seed bookmarks
                bookmarks_created = self.seed_bookmarks(content, users, bookmarks_per_content)
                total_bookmarks += bookmarks_created
                
                self.stdout.write(
                    f'  ✓ {comments_created} comments, {likes_created} likes, {bookmarks_created} bookmarks'
                )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎉 Seeding Complete!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'📊 Total Comments Created: {total_comments}')
        self.stdout.write(f'❤️  Total Likes Created: {total_likes}')
        self.stdout.write(f'🔖 Total Bookmarks Created: {total_bookmarks}')
        self.stdout.write(f'📄 Content Items Seeded: {content_count}')
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

    def create_fake_users(self, count):
        """Create fake users for testing"""
        created = []
        for i in range(count):
            try:
                user = User.objects.create_user(
                    email=fake.email(),
                    password='password123',
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_active=True
                )
                created.append(user)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  Failed to create user: {e}'))
        return created

    def seed_comments(self, content, users, count):
        """Seed comments for content"""
        created = 0
        comment_templates = [
            "Great content! Very helpful.",
            "Thanks for sharing this.",
            "Interesting perspective on this topic.",
            "This really helped me understand the concept.",
            "Well explained and detailed.",
            "Could you provide more examples?",
            "Excellent resource!",
            "Very informative, thank you!",
            "This is exactly what I was looking for.",
            "Clear and concise explanation.",
            "I have a question about this...",
            "This helped me a lot with my studies.",
            "Good work!",
            "Very useful information.",
            "Can you elaborate more on this?",
        ]
        
        # Randomly select users for comments (avoid duplicates)
        selected_users = random.sample(users, min(count, len(users)))
        
        for user in selected_users:
            try:
                comment_text = random.choice(comment_templates)
                # Add some variation
                if random.random() > 0.7:
                    comment_text += f" {fake.sentence()}"
                
                HubComment.objects.create(
                    content=content,
                    author=user,
                    comment_text=comment_text
                )
                created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Failed to create comment: {e}'))
        
        return created

    def seed_likes(self, content, users, count):
        """Seed likes for content"""
        created = 0
        
        # Randomly select users for likes (avoid duplicates)
        selected_users = random.sample(users, min(count, len(users)))
        
        for user in selected_users:
            try:
                ContentLike.objects.get_or_create(
                    content=content,
                    user=user
                )
                created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Failed to create like: {e}'))
        
        return created

    def seed_bookmarks(self, content, users, count):
        """Seed bookmarks for content"""
        created = 0
        
        # Randomly select users for bookmarks (avoid duplicates)
        selected_users = random.sample(users, min(count, len(users)))
        
        for user in selected_users:
            try:
                ContentBookmark.objects.get_or_create(
                    content=content,
                    user=user
                )
                created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Failed to create bookmark: {e}'))
        
        return created
