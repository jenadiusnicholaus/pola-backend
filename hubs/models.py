from django.db import models
from authentication.models import PolaUser
from django.utils import timezone


# ============================================================================
# SHARED HUB MODELS - Used across Advocates Hub, Students Hub, Forums, etc.
# ============================================================================
# These models use LearningMaterial as the unified content model for:
# - Text posts (discussions, questions, articles, news)
# - File documents (study materials, research papers)
# - Mixed content (posts with file attachments)
#
# Filter by hub_type to separate content between different hubs
# ============================================================================


class HubComment(models.Model):
    """
    Generic comment model that can be used across all hubs
    Supports nested replies and document attachments
    
    Now references LearningMaterial (unified content model) instead of HubPost
    """
    HUB_TYPES = [
        ('advocates', 'Advocates Hub'),
        ('students', 'Students Hub'),
        ('forum', 'Forum'),
        ('legal_ed', 'Legal Education'),
    ]
    
    # Comment metadata
    hub_type = models.CharField(max_length=20, choices=HUB_TYPES, db_index=True)
    content = models.ForeignKey(
        'documents.LearningMaterial',
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The post/document being commented on"
    )
    author = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='hub_comments')
    
    # Nested replies
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Content
    comment_text = models.TextField()
    
    # Optional document attachments
    documents = models.ManyToManyField(
        'documents.LearningMaterial',
        blank=True,
        related_name='attached_in_comments',
        help_text="Documents attached to this comment"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Hub Comment'
        verbose_name_plural = 'Hub Comments'
        indexes = [
            models.Index(fields=['hub_type', 'content', 'created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.hub_type}] Comment by {self.author.get_full_name()}"
    
    def get_likes_count(self):
        return self.likes.count()
    
    def get_replies_count(self):
        return self.replies.count()


class ContentLike(models.Model):
    """
    Track who liked which content (posts/documents) across all hubs
    Replaces HubPostLike - now unified for all content types
    """
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='content_likes')
    content = models.ForeignKey(
        'documents.LearningMaterial',
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'content']
        verbose_name = 'Content Like'
        verbose_name_plural = 'Content Likes'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['content', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} liked {self.content.title}"


class HubCommentLike(models.Model):
    """Track who liked which comment across all hubs"""
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='hub_comment_likes')
    comment = models.ForeignKey(HubComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
        verbose_name = 'Comment Like'
        verbose_name_plural = 'Comment Likes'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} liked comment"


class ContentBookmark(models.Model):
    """
    Track bookmarked content (posts/documents) across all hubs
    Replaces HubPostBookmark - now unified for all content types
    """
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='content_bookmarks')
    content = models.ForeignKey(
        'documents.LearningMaterial',
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'content']
        verbose_name = 'Content Bookmark'
        verbose_name_plural = 'Content Bookmarks'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} bookmarked {self.content.title}"


class HubMessage(models.Model):
    """
    Private messages between users across all hubs
    Can be hub-specific or general messages
    """
    HUB_TYPES = [
        ('advocates', 'Advocates Hub'),
        ('students', 'Students Hub'),
        ('forum', 'Forum'),
        ('general', 'General'),
    ]
    
    hub_type = models.CharField(max_length=20, choices=HUB_TYPES, default='general', db_index=True)
    sender = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='sent_hub_messages')
    recipient = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='received_hub_messages')
    
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
            models.Index(fields=['hub_type', 'recipient', '-created_at']),
            models.Index(fields=['hub_type', 'sender', '-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.hub_type}] {self.sender.get_full_name()} → {self.recipient.get_full_name()}"


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
        """Count total materials: direct topic materials + all subtopic materials"""
        from documents.models import LearningMaterial
        
        # Count direct materials linked to this topic
        direct_materials_count = LearningMaterial.objects.filter(topic=self).count()
        
        # Count materials in subtopics (for backward compatibility)
        subtopic_ids = self.subtopics.values_list('id', flat=True)
        subtopic_materials_count = LearningMaterial.objects.filter(subtopic_id__in=subtopic_ids).count()
        
        return direct_materials_count + subtopic_materials_count
    
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
# STUDENTS & LECTURERS HUB - Comments Tracking
# ============================================================================
# NOTE: We use LearningMaterial from documents app for document storage.
# LearningMaterial already handles:
# - Student/Lecturer/Admin uploads
# - Pricing (variable based on uploader_type)
# - Revenue splits (50/50 for students, 60/40 for lecturers, 55/45 for advocates)
# - File storage and downloads tracking via LearningMaterialPurchase
# - Categorization and search
#
# DEPRECATED: StudentHubDownload - Use LearningMaterialPurchase instead
# - LearningMaterialPurchase is the unified model for all purchases/downloads
# - It tracks buyer, material, amount_paid, download_count, last_downloaded
# - Works across all hubs (students, advocates, forum, legal_ed)
# ============================================================================


# DEPRECATED: Use LearningMaterialPurchase from documents app instead
# This model will be removed in a future migration
class StudentHubDownload(models.Model):
    """
    DEPRECATED: Use LearningMaterialPurchase from documents.models instead
    
    Track who downloaded what in Students Hub
    Links to LearningMaterial from documents app
    """
    material = models.ForeignKey(
        'documents.LearningMaterial', 
        on_delete=models.CASCADE, 
        related_name='student_hub_downloads_deprecated'
    )
    downloader = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='student_hub_downloads_deprecated')
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    download_count = models.IntegerField(default=0, help_text="Number of times re-downloaded")
    created_at = models.DateTimeField(auto_now_add=True)
    last_downloaded_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['material', 'downloader']
        ordering = ['-created_at']
        verbose_name = 'Student Hub Download (Deprecated)'
        verbose_name_plural = 'Student Hub Downloads (Deprecated)'
    
    def __str__(self):
        return f"{self.downloader.get_full_name()} downloaded {self.material.title}"
    
    def increment_download(self):
        """Track re-downloads"""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save()




# DEPRECATED: Use HubComment instead
# This model will be removed in a future migration  
class StudentHubComment(models.Model):
    """
    DEPRECATED: Use HubComment from hubs.models instead
    
    Comments on learning materials in Students Hub
    Supports replies (nested comments)
    Links to LearningMaterial from documents app
    """
    material = models.ForeignKey(
        'documents.LearningMaterial',
        on_delete=models.CASCADE,
        related_name='student_hub_comments_deprecated'
    )
    author = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='student_hub_comments_deprecated')
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        help_text="Parent comment if this is a reply"
    )
    
    content = models.TextField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Document Comment (Deprecated)'
        verbose_name_plural = 'Document Comments (Deprecated)'
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.material.title}"
    
    def get_likes_count(self):
        """Get total likes count"""
        return self.likes.count()
    
    def get_replies_count(self):
        """Get total replies count"""
        return self.replies.count()


# DEPRECATED: Use HubCommentLike instead
class StudentHubCommentLike(models.Model):
    """
    DEPRECATED: Use HubCommentLike instead
    Track who liked which comment/reply
    """
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(StudentHubComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
        verbose_name = 'Document Comment Like (Deprecated)'
        verbose_name_plural = 'Document Comment Likes (Deprecated)'



class StudentHubCommentLike(models.Model):
    """Track who liked which comment/reply"""
    user = models.ForeignKey(PolaUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(StudentHubComment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
        verbose_name = 'Comment Like'
        verbose_name_plural = 'Comment Likes'