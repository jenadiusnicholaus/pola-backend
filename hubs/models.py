from django.db import models
from authentication.models import PolaUser
from django.utils import timezone


# ============================================================================
# LEGAL EDUCATION HUB - Topics & Subtopics (Educational Content)
# ============================================================================

class LegalEdTopic(models.Model):
    """
    Topic for Legal Education Hub only
    Main category (e.g., Constitutional Law, Criminal Law, etc.)
    """
    name = models.CharField(max_length=255, help_text="Topic name in English")
    name_sw = models.CharField(max_length=255, blank=True, null=True, help_text="Topic name in Swahili")
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="URL-friendly identifier")
    
    description = models.TextField(blank=True, null=True, help_text="Topic description in English")
    description_sw = models.TextField(blank=True, null=True, help_text="Topic description in Swahili")
    
    icon = models.CharField(max_length=100, blank=True, help_text="Icon for this topic")
    display_order = models.IntegerField(default=0, help_text="Display order")
    
    is_active = models.BooleanField(default=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    class Meta:
        verbose_name = "Legal Education Topic"
        verbose_name_plural = "Legal Education Topics"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name
    
    def get_subtopics_count(self):
        """Get number of subtopics"""
        return self.subtopics.count()
    
    def get_materials_count(self):
        """Count total materials in all subtopics under this topic"""
        from documents.models import LearningMaterial
        
        subtopic_ids = self.subtopics.values_list('id', flat=True)
        return LearningMaterial.objects.filter(subtopic_id__in=subtopic_ids).count()
    
class LegalEdSubTopic(models.Model):
    """
    Subtopic - Specific subject within a topic (e.g., Fundamental Rights, Bill of Rights, etc.)
    Each subtopic contains learning materials
    """
    topic = models.ForeignKey(LegalEdTopic, on_delete=models.CASCADE, related_name='subtopics')
    
    name = models.CharField(max_length=255, help_text="Subtopic name in English")
    name_sw = models.CharField(max_length=255, blank=True, null=True, help_text="Subtopic name in Swahili")
    slug = models.SlugField(max_length=255, blank=True, help_text="URL-friendly identifier")
    
    description = models.TextField(blank=True, null=True, help_text="Subtopic description in English")
    description_sw = models.TextField(blank=True, null=True, help_text="Subtopic description in Swahili")
    
    display_order = models.IntegerField(default=0, help_text="Display order within topic")
    
    is_active = models.BooleanField(default=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    class Meta:
        verbose_name = "SubTopic"
        verbose_name_plural = "SubTopics"
        ordering = ['topic', 'display_order', 'name']
        unique_together = ['topic', 'slug']

    def __str__(self):
        return f"{self.topic.name} - {self.name}"
    
    def get_materials_count(self):
        """Get number of materials in this subtopic"""
        return self.materials.count()
    
    def get_materials_by_language(self, language='en'):
        """Get materials filtered by language"""
        return self.materials.filter(language=language, is_active=True, is_approved=True)


# ============================================================================
# ADVOCATES HUB - Social Feed for Advocates Only
# ============================================================================

class AdvocatePost(models.Model):
    """
    Posts in Advocates Hub - Only advocates can create posts
    Admins can also post articles, news, attachments
    """
    POST_TYPES = [
        ('discussion', 'Discussion Post'),
        ('article', 'Article (Admin)'),
        ('news', 'News (Admin)'),
        ('announcement', 'Announcement'),
    ]
    
    author = models.ForeignKey(
        PolaUser, 
        on_delete=models.CASCADE, 
        related_name='advocate_posts',
        help_text="Post author (must be advocate or admin)"
    )
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='discussion')
    
    # Content
    title = models.CharField(max_length=500, blank=True, help_text="Post title (optional)")
    content = models.TextField(help_text="Post text content")
    
    # Media attachments
    documents = models.ManyToManyField(
        'AdvocateDocument', 
        blank=True, 
        related_name='posts',
        help_text="Attached documents"
    )
    video_url = models.URLField(blank=True, null=True, help_text="Video link (YouTube, etc) - playable on screen")
    
    # Engagement
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    bookmarks_count = models.IntegerField(default=0)
    
    # Moderation
    is_pinned = models.BooleanField(default=False, help_text="Pin post to top")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Advocate Post'
        verbose_name_plural = 'Advocate Posts'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.author.get_full_name()} - {self.title or self.content[:50]}"
    
    def increment_likes(self):
        self.likes_count += 1
        self.save()
    
    def decrement_likes(self):
        self.likes_count = max(0, self.likes_count - 1)
        self.save()
    
    def increment_comments(self):
        self.comments_count += 1
        self.save()
    
    def increment_bookmarks(self):
        self.bookmarks_count += 1
        self.save()


class AdvocateDocument(models.Model):
    """
    Documents that can be uploaded and attached to posts
    """
    uploader = models.ForeignKey(
        PolaUser, 
        on_delete=models.CASCADE, 
        related_name='advocate_documents'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='advocates_hub/documents/')
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, blank=True, help_text="MIME type")
    
    # Can be attached to posts or used standalone
    is_standalone = models.BooleanField(default=False, help_text="Not attached to any post")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Advocate Document'
        verbose_name_plural = 'Advocate Documents'
    
    def __str__(self):
        return f"{self.title} by {self.uploader.get_full_name()}"


class AdvocateComment(models.Model):
    """
    Comments on advocate posts
    Supports replies (nested comments)
    """
    post = models.ForeignKey(AdvocatePost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='advocate_comments')
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        help_text="Parent comment if this is a reply"
    )
    
    content = models.TextField()
    
    # Optional document attachment in comment/reply
    attached_documents = models.ManyToManyField(
        AdvocateDocument, 
        blank=True, 
        related_name='comments'
    )
    
    # Engagement
    likes_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Advocate Comment'
        verbose_name_plural = 'Advocate Comments'
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.post}"
    
    def increment_likes(self):
        self.likes_count += 1
        self.save()
    
    def get_replies_count(self):
        return self.replies.count()


class AdvocatePostLike(models.Model):
    """Track who liked which post"""
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE)
    post = models.ForeignKey(AdvocatePost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Post Like'
        verbose_name_plural = 'Post Likes'


class AdvocateCommentLike(models.Model):
    """Track who liked which comment"""
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(AdvocateComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
        verbose_name = 'Comment Like'
        verbose_name_plural = 'Comment Likes'


class AdvocatePostBookmark(models.Model):
    """Track bookmarked posts"""
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='advocate_bookmarks')
    post = models.ForeignKey(AdvocatePost, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Post Bookmark'
        verbose_name_plural = 'Post Bookmarks'


class AdvocateMessage(models.Model):
    """
    Private messages between advocates
    """
    sender = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='sent_advocate_messages')
    recipient = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='received_advocate_messages')
    
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Private Message'
        verbose_name_plural = 'Private Messages'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} to {self.recipient.get_full_name()}"


# ============================================================================
# STUDENTS & LECTURERS HUB - Comments & Downloads Tracking
# ============================================================================
# NOTE: We use LearningMaterial from documents app for document storage.
# LearningMaterial already handles:
# - Student/Lecturer/Admin uploads
# - Pricing (student: 1500, lecturer: 5000, admin: 3000)
# - Revenue splits (50/50 for students, 60/40 for lecturers)
# - File storage and downloads tracking
# - Categorization and search
#
# These models only track Students Hub-specific UI interactions:
# - Download history (who downloaded what)
# - Comments on materials

class StudentHubDownload(models.Model):
    """
    Track who downloaded what in Students Hub
    Links to LearningMaterial from documents app
    """
    material = models.ForeignKey(
        'documents.LearningMaterial', 
        on_delete=models.CASCADE, 
        related_name='student_hub_downloads'
    )
    downloader = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='student_hub_downloads')
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    download_count = models.IntegerField(default=0, help_text="Number of times re-downloaded")
    created_at = models.DateTimeField(auto_now_add=True)
    last_downloaded_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['material', 'downloader']
        ordering = ['-created_at']
        verbose_name = 'Student Hub Download'
        verbose_name_plural = 'Student Hub Downloads'
    
    def __str__(self):
        return f"{self.downloader.get_full_name()} downloaded {self.material.title}"
    
    def increment_download(self):
        """Track re-downloads"""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save()


class StudentHubComment(models.Model):
    """
    Comments on learning materials in Students Hub
    Supports replies (nested comments)
    Links to LearningMaterial from documents app
    """
    material = models.ForeignKey(
        'documents.LearningMaterial',
        on_delete=models.CASCADE,
        related_name='student_hub_comments'
    )
    author = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='student_hub_comments')
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        help_text="Parent comment if this is a reply"
    )
    
    content = models.TextField()
    
    # Engagement
    likes_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Document Comment'
        verbose_name_plural = 'Document Comments'
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.material.title}"
    
    def increment_likes(self):
        self.likes_count += 1
        self.save()


class StudentHubCommentLike(models.Model):
    """Track who liked which comment/reply"""
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(StudentHubComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
        verbose_name = 'Comment Like'
        verbose_name_plural = 'Comment Likes'