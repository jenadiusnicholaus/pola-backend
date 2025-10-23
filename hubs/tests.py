from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from hubs.models import (
    HubComment, ContentLike, ContentBookmark, HubMessage
)
from documents.models import LearningMaterial
from datetime import datetime, timedelta

User = get_user_model()


class AdminHubEngagementTestCase(APITestCase):
    """Test suite for admin engagement viewing endpoints"""

    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )

        # Create regular users for engagement
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='pass123',
            first_name='John',
            last_name='Doe'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='pass123',
            first_name='Jane',
            last_name='Smith'
        )
        self.user3 = User.objects.create_user(
            email='user3@test.com',
            password='pass123',
            first_name='Bob',
            last_name='Johnson'
        )

        # Create hubs - not needed as we're using LearningMaterial directly

        # Create test content
        self.content = LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='advocates',
            content_type='discussion',
            title='Test Content',
            content='Test content for engagement',
            is_active=True
        )

        # Create comments
        self.comment1 = HubComment.objects.create(
            content=self.content,
            author=self.user1,
            comment_text='Great post!'
        )
        self.comment2 = HubComment.objects.create(
            content=self.content,
            author=self.user2,
            comment_text='Very helpful, thanks!'
        )
        self.comment3 = HubComment.objects.create(
            content=self.content,
            author=self.user3,
            comment_text='Interesting perspective'
        )

        # Create likes
        self.like1 = ContentLike.objects.create(
            content=self.content,
            user=self.user1
        )
        self.like2 = ContentLike.objects.create(
            content=self.content,
            user=self.user2
        )

        # Create bookmarks
        self.bookmark1 = ContentBookmark.objects.create(
            content=self.content,
            user=self.user1
        )

        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_get_content_comments_list(self):
        """Test retrieving paginated comments for content"""
        url = reverse('admin-hub-content-comments', kwargs={'pk': self.content.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
        
        # Verify comment structure
        first_comment = response.data['results'][0]
        self.assertIn('id', first_comment)
        self.assertIn('author', first_comment)
        self.assertIn('comment_text', first_comment)
        self.assertIn('created_at', first_comment)
        self.assertIn('likes_count', first_comment)

    def test_get_content_comments_pagination(self):
        """Test comments pagination"""
        # Create more comments to test pagination
        for i in range(25):
            HubComment.objects.create(
                content=self.content,
                author=self.user1,
                comment_text=f'Comment {i}'
            )

        url = reverse('admin-hub-content-comments', kwargs={'pk': self.content.id})
        response = self.client.get(url, {'page': 1, 'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])

    def test_get_content_likes_list(self):
        """Test retrieving paginated likes for content"""
        url = reverse('admin-hub-content-likes', kwargs={'pk': self.content.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify like structure
        first_like = response.data['results'][0]
        self.assertIn('id', first_like)
        self.assertIn('user_id', first_like)
        self.assertIn('user_email', first_like)
        self.assertIn('user_name', first_like)
        self.assertIn('created_at', first_like)

    def test_get_content_bookmarks_list(self):
        """Test retrieving paginated bookmarks for content"""
        url = reverse('admin-hub-content-bookmarks', kwargs={'pk': self.content.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        
        # Verify bookmark structure
        first_bookmark = response.data['results'][0]
        self.assertIn('user_name', first_bookmark)
        self.assertEqual(first_bookmark['user_email'], 'user1@test.com')

    def test_get_content_engagement_summary(self):
        """Test retrieving engagement summary"""
        url = reverse('admin-hub-content-engagement', kwargs={'pk': self.content.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify summary structure
        self.assertIn('total_comments', response.data)
        self.assertIn('total_likes', response.data)
        self.assertIn('total_bookmarks', response.data)
        self.assertIn('recent_comments', response.data)
        self.assertIn('recent_likes', response.data)
        
        # Verify counts
        self.assertEqual(response.data['total_comments'], 3)
        self.assertEqual(response.data['total_likes'], 2)
        self.assertEqual(response.data['total_bookmarks'], 1)
        
        # Verify recent activity (max 10)
        self.assertLessEqual(len(response.data['recent_comments']), 10)
        self.assertLessEqual(len(response.data['recent_likes']), 10)

    def test_engagement_endpoints_require_admin(self):
        """Test that engagement endpoints require admin authentication"""
        # Create regular user client
        regular_client = APIClient()
        regular_client.force_authenticate(user=self.user1)

        endpoints = [
            reverse('admin-hub-content-comments', kwargs={'pk': self.content.id}),
            reverse('admin-hub-content-likes', kwargs={'pk': self.content.id}),
            reverse('admin-hub-content-bookmarks', kwargs={'pk': self.content.id}),
            reverse('admin-hub-content-engagement', kwargs={'pk': self.content.id}),
        ]

        for url in endpoints:
            response = regular_client.get(url)
            self.assertEqual(
                response.status_code, 
                status.HTTP_403_FORBIDDEN,
                f"Endpoint {url} should require admin access"
            )

    def test_engagement_endpoints_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        unauth_client = APIClient()
        
        url = reverse('admin-hub-content-comments', kwargs={'pk': self.content.id})
        response = unauth_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_engagement_nonexistent_content(self):
        """Test engagement endpoints with non-existent content"""
        url = reverse('admin-hub-content-engagement', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_engagement_no_activity(self):
        """Test engagement summary for content with no engagement"""
        # Create content with no engagement
        empty_content = LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='forum',
            content_type='discussion',
            title='Empty Content',
            content='Empty content',
            is_active=True
        )

        url = reverse('admin-hub-content-engagement', kwargs={'pk': empty_content.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_comments'], 0)
        self.assertEqual(response.data['total_likes'], 0)
        self.assertEqual(response.data['total_bookmarks'], 0)
        self.assertEqual(len(response.data['recent_comments']), 0)
        self.assertEqual(len(response.data['recent_likes']), 0)


class AdminHubContentManagementTestCase(APITestCase):
    """Test suite for admin content management"""

    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_list_hub_content(self):
        """Test listing all hub content"""
        # Create test content
        LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='advocates',
            content_type='discussion',
            title='Test Post',
            content='Test post'
        )
        
        url = reverse('admin-hub-content-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_filter_by_hub_type(self):
        """Test filtering content by hub type"""
        LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='advocates',
            content_type='discussion',
            title='Advocates Post',
            content='Advocates post'
        )
        LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='students',
            content_type='discussion',
            title='Students Post',
            content='Students post'
        )

        url = reverse('admin-hub-content-list')
        response = self.client.get(url, {'hub_type': 'advocates'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['results']:
            self.assertEqual(item['hub_type'], 'advocates')

    def test_pin_content(self):
        """Test pinning content"""
        content = LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='forum',
            content_type='discussion',
            title='Test Post',
            content='Test post',
            is_pinned=False
        )

        url = reverse('admin-hub-content-pin', kwargs={'pk': content.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content.refresh_from_db()
        self.assertTrue(content.is_pinned)

    def test_toggle_active(self):
        """Test toggling content active status"""
        content = LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='legal_ed',
            content_type='discussion',
            title='Test Post',
            content='Test post',
            is_active=True
        )

        url = reverse('admin-hub-content-toggle-active', kwargs={'pk': content.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content.refresh_from_db()
        self.assertFalse(content.is_active)

    def test_bulk_delete(self):
        """Test bulk delete operation"""
        content1 = LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='forum',
            content_type='discussion',
            title='Post 1',
            content='Post 1'
        )
        content2 = LearningMaterial.objects.create(
            uploader=self.admin_user,
            uploader_type='admin',
            hub_type='forum',
            content_type='discussion',
            title='Post 2',
            content='Post 2'
        )

        url = reverse('admin-hub-content-bulk-delete')
        response = self.client.post(url, {'ids': [content1.id, content2.id]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LearningMaterial.objects.filter(
            id__in=[content1.id, content2.id]
        ).count(), 0)

    def test_statistics(self):
        """Test statistics endpoint"""
        url = reverse('admin-hub-content-statistics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_content', response.data)
        self.assertIn('by_hub_type', response.data)
        self.assertIn('by_content_type', response.data)
