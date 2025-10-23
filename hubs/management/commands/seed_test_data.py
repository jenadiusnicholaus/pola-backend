"""
Django management command to seed complete test data:
- Content/Posts
- Users (if needed)
- Comments
- Likes
- Bookmarks

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --content=20 --users=30
    python manage.py seed_test_data --hub-type=students
    python manage.py seed_test_data --clear
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from documents.models import LearningMaterial
from hubs.models import HubComment, ContentLike, ContentBookmark
from django.db import transaction
import random
from faker import Faker
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seed complete test data: content, users, comments, likes, bookmarks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--content',
            type=int,
            default=15,
            help='Number of content items to create (default: 15)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create (default: 20)'
        )
        parser.add_argument(
            '--hub-type',
            type=str,
            default=None,
            help='Create content only for specific hub (advocates, students, forum, legal_ed)'
        )
        parser.add_argument(
            '--comments-range',
            type=str,
            default='3-10',
            help='Range of comments per content (e.g., 3-10, default: 3-10)'
        )
        parser.add_argument(
            '--likes-range',
            type=str,
            default='5-20',
            help='Range of likes per content (e.g., 5-20, default: 5-20)'
        )
        parser.add_argument(
            '--bookmarks-range',
            type=str,
            default='1-5',
            help='Range of bookmarks per content (e.g., 1-5, default: 1-5)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before seeding (CAUTION!)'
        )

    def handle(self, *args, **options):
        content_count = options['content']
        users_count = options['users']
        hub_type = options['hub_type']
        clear = options['clear']
        
        # Parse ranges
        comments_min, comments_max = map(int, options['comments_range'].split('-'))
        likes_min, likes_max = map(int, options['likes_range'].split('-'))
        bookmarks_min, bookmarks_max = map(int, options['bookmarks_range'].split('-'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🌱 POLA BACKEND - TEST DATA SEEDING'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Clear existing data if requested
        if clear:
            self.stdout.write(self.style.WARNING('⚠️  CLEARING ALL TEST DATA...'))
            if input('Are you sure? Type "yes" to confirm: ').lower() == 'yes':
                self.clear_all_data()
                self.stdout.write(self.style.SUCCESS('✅ Data cleared\n'))
            else:
                self.stdout.write(self.style.ERROR('❌ Cancelled\n'))
                return

        # Step 1: Create Users
        self.stdout.write(self.style.HTTP_INFO('STEP 1: Creating Users'))
        self.stdout.write('-' * 70)
        users = self.create_users(users_count)
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(users)} users\n'))

        # Step 2: Create Content
        self.stdout.write(self.style.HTTP_INFO('STEP 2: Creating Content/Posts'))
        self.stdout.write('-' * 70)
        content_items = self.create_content(content_count, users, hub_type)
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(content_items)} content items\n'))

        # Step 3: Seed Engagement
        self.stdout.write(self.style.HTTP_INFO('STEP 3: Adding Engagement (Comments, Likes, Bookmarks)'))
        self.stdout.write('-' * 70)
        
        total_comments = 0
        total_likes = 0
        total_bookmarks = 0

        for idx, content in enumerate(content_items, 1):
            # Random counts within ranges
            num_comments = random.randint(comments_min, comments_max)
            num_likes = random.randint(likes_min, likes_max)
            num_bookmarks = random.randint(bookmarks_min, bookmarks_max)
            
            self.stdout.write(
                f'  [{idx}/{len(content_items)}] {content.title[:40]}...'
            )
            
            # Add engagement
            comments = self.add_comments(content, users, num_comments)
            likes = self.add_likes(content, users, num_likes)
            bookmarks = self.add_bookmarks(content, users, num_bookmarks)
            
            total_comments += comments
            total_likes += likes
            total_bookmarks += bookmarks
            
            self.stdout.write(
                f'      💬 {comments} comments | ❤️  {likes} likes | 🔖 {bookmarks} bookmarks'
            )

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('🎉 SEEDING COMPLETE!'))
        self.stdout.write('='*70)
        self.stdout.write(f'👥 Users Created: {len(users)}')
        self.stdout.write(f'📄 Content Items: {len(content_items)}')
        self.stdout.write(f'💬 Total Comments: {total_comments}')
        self.stdout.write(f'❤️  Total Likes: {total_likes}')
        self.stdout.write(f'🔖 Total Bookmarks: {total_bookmarks}')
        self.stdout.write('='*70)
        
        # Quick test URLs
        if content_items:
            first_content_id = content_items[0].id
            self.stdout.write(self.style.HTTP_INFO('\n📍 Test URLs:'))
            self.stdout.write(f'   View Content: /api/v1/admin/hubs/hub-content/{first_content_id}/')
            self.stdout.write(f'   Comments: /api/v1/admin/hubs/hub-content/{first_content_id}/comments/')
            self.stdout.write(f'   Engagement: /api/v1/admin/hubs/hub-content/{first_content_id}/engagement/')
            self.stdout.write(f'   Swagger: http://localhost:8000/swagger/')
        
        self.stdout.write('\n')

    def clear_all_data(self):
        """Clear all test data"""
        with transaction.atomic():
            comments = HubComment.objects.all().delete()[0]
            likes = ContentLike.objects.all().delete()[0]
            bookmarks = ContentBookmark.objects.all().delete()[0]
            content = LearningMaterial.objects.all().delete()[0]
            users = User.objects.filter(email__contains='@example.com').delete()[0]
            
            self.stdout.write(f'   Deleted: {comments} comments, {likes} likes, {bookmarks} bookmarks')
            self.stdout.write(f'   Deleted: {content} content items, {users} test users')

    def create_users(self, count):
        """Create test users"""
        existing_users = list(User.objects.filter(is_active=True))
        
        if len(existing_users) >= count:
            self.stdout.write(f'   Using {count} existing users')
            return random.sample(existing_users, count)
        
        users = existing_users.copy()
        to_create = count - len(existing_users)
        
        self.stdout.write(f'   Creating {to_create} new users...')
        
        user_types = ['student', 'lecturer', 'advocate', 'admin']
        
        for i in range(to_create):
            try:
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
                
                user = User.objects.create_user(
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    agreed_to_Terms=True  # Required field
                )
                users.append(user)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  Failed to create user: {e}'))
        
        return users

    def create_content(self, count, users, hub_type=None):
        """Create content/posts"""
        content_items = []
        
        # Hub types to create
        if hub_type:
            hub_types = [hub_type]
        else:
            hub_types = ['advocates', 'students', 'forum', 'legal_ed']
        
        # Content type distribution per hub
        hub_content_types = {
            'advocates': ['discussion', 'article', 'news', 'announcement'],
            'students': ['document', 'notes', 'past_papers', 'tutorial'],
            'forum': ['discussion', 'question', 'article'],
            'legal_ed': ['article', 'tutorial', 'case_study', 'research'],
        }
        
        # Titles templates
        title_templates = {
            'advocates': [
                "Understanding {} in Legal Practice",
                "Recent Developments in {}",
                "Case Analysis: {}",
                "Professional Guide to {}",
                "Legal Updates on {}",
            ],
            'students': [
                "Study Notes: {}",
                "Complete Guide to {}",
                "Exam Preparation: {}",
                "Tutorial on {}",
                "Past Papers: {}",
            ],
            'forum': [
                "Discussion: {}",
                "Question about {}",
                "Debate: {}",
                "Your thoughts on {}?",
                "Help needed with {}",
            ],
            'legal_ed': [
                "Introduction to {}",
                "Advanced {}",
                "Case Study: {}",
                "Research on {}",
                "Comprehensive Guide to {}",
            ],
        }
        
        # Topics
        topics = [
            "Contract Law", "Criminal Law", "Constitutional Law", "Property Law",
            "Corporate Law", "Family Law", "International Law", "Human Rights",
            "Legal Ethics", "Evidence Law", "Civil Procedure", "Legal Research",
            "Administrative Law", "Tax Law", "Labor Law", "Environmental Law"
        ]
        
        items_per_hub = count // len(hub_types)
        
        for hub in hub_types:
            self.stdout.write(f'   Creating {items_per_hub} items for {hub} hub...')
            
            for i in range(items_per_hub):
                try:
                    # Random selections
                    content_type = random.choice(hub_content_types[hub])
                    uploader = random.choice(users)
                    topic = random.choice(topics)
                    title_template = random.choice(title_templates[hub])
                    title = title_template.format(topic)
                    
                    # Content text
                    content_text = self.generate_content_text(hub, topic)
                    
                    # Price and downloadable logic
                    if hub == 'students' and content_type in ['document', 'notes', 'past_papers']:
                        price = random.choice([0, 500, 1000, 1500, 2000, 3000])
                        is_downloadable = True
                    else:
                        price = 0  # Free for non-document content
                        is_downloadable = False
                    
                    # Create content
                    from decimal import Decimal
                    content = LearningMaterial.objects.create(
                        hub_type=hub,
                        content_type=content_type,
                        uploader=uploader,
                        uploader_type=random.choice(['student', 'lecturer', 'advocate', 'admin']),
                        title=title,
                        content=content_text,
                        description=f"This is a comprehensive resource on {topic.lower()}. " + fake.sentence(),
                        is_active=True,
                        is_pinned=random.random() < 0.1,  # 10% pinned
                        is_downloadable=is_downloadable,
                        price=Decimal(str(price)),
                        views_count=random.randint(0, 500),
                        downloads_count=random.randint(0, 50) if is_downloadable else 0,
                        created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                    )
                    content_items.append(content)
                    
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Failed to create content: {e}'))
        
        return content_items

    def generate_content_text(self, hub, topic):
        """Generate realistic content text"""
        intros = [
            f"This comprehensive guide covers the essential aspects of {topic}.",
            f"Understanding {topic} is crucial for legal professionals.",
            f"In this resource, we explore the key principles of {topic}.",
            f"A detailed examination of {topic} and its applications.",
        ]
        
        bodies = [
            f"{fake.paragraph(nb_sentences=3)} {fake.paragraph(nb_sentences=4)}",
            f"{fake.paragraph(nb_sentences=2)} {fake.paragraph(nb_sentences=3)} {fake.paragraph(nb_sentences=2)}",
            f"{fake.paragraph(nb_sentences=4)} {fake.paragraph(nb_sentences=3)}",
        ]
        
        conclusions = [
            "This resource provides valuable insights for both students and practitioners.",
            "Understanding these principles is essential for success in this area.",
            "We hope this guide helps clarify these important concepts.",
            "For more information, please refer to the recommended reading list.",
        ]
        
        return f"{random.choice(intros)}\n\n{random.choice(bodies)}\n\n{random.choice(conclusions)}"

    def add_comments(self, content, users, count):
        """Add comments to content"""
        if count == 0:
            return 0
        
        comment_templates = [
            "This is really helpful, thank you for sharing!",
            "Great explanation! Very clear and concise.",
            "Could you provide more examples on this topic?",
            "Excellent resource! Exactly what I was looking for.",
            "Thanks for posting this. Very informative.",
            "I have a question about this section...",
            "This helped me understand the concept much better.",
            "Well written and thoroughly researched.",
            "Appreciate the detailed breakdown.",
            "Very useful for my studies!",
            "Clear and easy to understand.",
            "Thanks for sharing your knowledge!",
            "This clarified a lot of doubts I had.",
            "Great content! Keep it up.",
            "Bookmarking this for later reference.",
        ]
        
        created = 0
        selected_users = random.sample(users, min(count, len(users)))
        
        for user in selected_users:
            try:
                comment_text = random.choice(comment_templates)
                if random.random() > 0.6:
                    comment_text += f" {fake.sentence()}"
                
                HubComment.objects.create(
                    content=content,
                    author=user,
                    comment_text=comment_text,
                    created_at=content.created_at + timedelta(days=random.randint(0, 30))
                )
                created += 1
            except:
                pass
        
        return created

    def add_likes(self, content, users, count):
        """Add likes to content"""
        if count == 0:
            return 0
        
        created = 0
        selected_users = random.sample(users, min(count, len(users)))
        
        for user in selected_users:
            try:
                ContentLike.objects.get_or_create(
                    content=content,
                    user=user,
                    defaults={'created_at': content.created_at + timedelta(days=random.randint(0, 30))}
                )
                created += 1
            except:
                pass
        
        return created

    def add_bookmarks(self, content, users, count):
        """Add bookmarks to content"""
        if count == 0:
            return 0
        
        created = 0
        selected_users = random.sample(users, min(count, len(users)))
        
        for user in selected_users:
            try:
                ContentBookmark.objects.get_or_create(
                    content=content,
                    user=user,
                    defaults={'created_at': content.created_at + timedelta(days=random.randint(0, 30))}
                )
                created += 1
            except:
                pass
        
        return created
