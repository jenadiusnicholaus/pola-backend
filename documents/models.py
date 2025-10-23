"""
Documents App - Learning Materials & Document Management

This app manages all document-related functionality including:
- Learning materials uploaded by students, lecturers, and admins
- Material purchases and downloads
- Revenue tracking and splits

Moved from subscriptions app for better separation of concerns.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from authentication.models import PolaUser


class LearningMaterial(models.Model):
    """
    Unified content model for all hubs (posts + documents)
    
    Supports:
    - Text posts (discussions, questions, articles) - usually free
    - File documents (notes, papers, research) - can be paid/free
    - Mixed content (posts with file attachments)
    
    Used by:
    - Advocates Hub: Discussions, articles, news with document attachments
    - Students Hub: Document marketplace with paid downloads
    - Community Forum: Public discussions and debates
    - Legal Education Hub: Admin-curated learning materials
    """
    
    # Hub Types
    HUB_TYPES = [
        ('advocates', 'Advocates Hub'),
        ('students', 'Students Hub'),
        ('forum', 'Community Forum'),
        ('legal_ed', 'Legal Education'),
    ]
    
    # Content Types (merged from post types and document types)
    CONTENT_TYPE_CHOICES = [
        # Post types (usually free, text-based)
        ('discussion', 'Discussion Post'),
        ('question', 'Question Post'),
        ('article', 'Article'),
        ('news', 'News'),
        ('announcement', 'Announcement'),
        
        # Document types (can be paid, file-based)
        ('document', 'General Document'),
        ('notes', 'Study Notes'),
        ('past_papers', 'Past Exam Papers'),
        ('assignments', 'Assignments'),
        ('research', 'Research Paper'),
        ('case_study', 'Case Study'),
        ('tutorial', 'Tutorial'),
        ('hub_content', 'Hub Content'),
        ('other', 'Other'),
    ]
    
    UPLOADER_TYPES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('advocate', 'Advocate'),
        ('admin', 'Admin'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
    ]
    
    # Core fields
    hub_type = models.CharField(
        max_length=20, 
        choices=HUB_TYPES,
        default='students',  # Default for existing documents
        db_index=True,
        help_text="Which hub this content belongs to"
    )
    content_type = models.CharField(
        max_length=20, 
        choices=CONTENT_TYPE_CHOICES,
        default='document',  # Default for existing files
        help_text="Type of content (post or document)"
    )
    
    uploader = models.ForeignKey(
        PolaUser, 
        on_delete=models.CASCADE, 
        related_name='uploaded_materials'
    )
    uploader_type = models.CharField(max_length=20, choices=UPLOADER_TYPES)
    
    # Categorization & Organization
    subtopic = models.ForeignKey(
        'hubs.LegalEdSubTopic', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='materials',
        help_text="Link to Legal Ed subtopic (for legal_ed hub only)"
    )
    
    # Content
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    content = models.TextField(
        blank=True,
        help_text="Rich text content for posts (HTML/Markdown)"
    )
    
    # Student-Lecturer Interaction (Students Hub specific)
    is_lecture_material = models.BooleanField(
        default=False,
        help_text="Indicates if this is official lecture material (uploaded by lecturer)"
    )
    is_verified_quality = models.BooleanField(
        default=False,
        help_text="Lecturer-verified or platform-verified quality content"
    )
    
    # File attachments (optional for posts, required for documents)
    file = models.FileField(
        upload_to='learning_materials/', 
        blank=True, 
        null=True, 
        help_text="File content (PDF, DOC, etc) - Optional for text posts"
    )
    file_size = models.BigIntegerField(
        default=0, 
        help_text="File size in bytes"
    )
    
    # Media
    video_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="Embedded video link (YouTube, Vimeo, etc)"
    )
    
    # Settings
    language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES, 
        default='en', 
        help_text="Content language"
    )
    is_downloadable = models.BooleanField(
        default=True, 
        help_text="Allow users to download this material"
    )
    
    # Pricing & Revenue
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0'),
        help_text="Price in TZS (0 = free)"
    )
    downloads_count = models.IntegerField(default=0)
    views_count = models.IntegerField(
        default=0,
        help_text="Number of times content was viewed (not downloaded)"
    )
    total_revenue = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0')
    )
    uploader_earnings = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0')
    )
    platform_earnings = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0'),
        help_text="Platform's share of revenue"
    )
    
    # Moderation
    is_approved = models.BooleanField(
        default=True, 
        help_text="Admin approval (auto-approve posts, review documents)"
    )
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(
        default=False, 
        help_text="Pin to top of feed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Hub Content'
        verbose_name_plural = 'Hub Contents'
        # IMPORTANT: Keep existing database table to avoid data migration
        db_table = 'subscriptions_learningmaterial'
        indexes = [
            models.Index(fields=['hub_type', 'content_type', '-created_at']),
            models.Index(fields=['uploader', '-created_at']),
            models.Index(fields=['price']),
            models.Index(fields=['is_approved', 'is_active']),
        ]
    
    def __str__(self):
        return f"[{self.hub_type}] {self.title}"
    
    def is_free(self):
        """Check if content is free"""
        return self.price == 0
    
    def is_post(self):
        """Check if this is a text post"""
        post_types = ['discussion', 'question', 'article', 'news', 'announcement']
        return self.content_type in post_types
    
    def is_document(self):
        """Check if this is a file document"""
        doc_types = ['document', 'notes', 'past_papers', 'assignments', 'research', 
                     'case_study', 'tutorial', 'hub_content', 'other']
        return self.content_type in doc_types
    
    def get_likes_count(self):
        """Get total likes"""
        return self.likes.count()
    
    def get_comments_count(self):
        """Get total comments"""
        return self.comments.count()
    
    def get_bookmarks_count(self):
        """Get total bookmarks"""
        return self.bookmarks.count()
    
    def get_revenue_split(self):
        """
        Get revenue split based on uploader type
        
        Returns:
            dict: {'uploader': float, 'app': float}
        """
        splits = {
            'student': {'uploader': 0.50, 'app': 0.50},   # 50% to student, 50% to app
            'lecturer': {'uploader': 0.60, 'app': 0.40},  # 60% to lecturer, 40% to app
            'advocate': {'uploader': 0.55, 'app': 0.45},  # 55% to advocate, 45% to app
            'admin': {'uploader': 0.00, 'app': 1.00},     # 100% to platform (admin materials are platform content)
        }
        return splits.get(self.uploader_type, {'uploader': 0.50, 'app': 0.50})
    
    def record_purchase(self, buyer):
        """
        Record a purchase/download and calculate revenue split
        
        Args:
            buyer (PolaUser): The user purchasing this material
        
        Returns:
            dict: {
                'uploader_share': Decimal,
                'app_share': Decimal,
                'purchase': LearningMaterialPurchase,
                'earning': UploaderEarnings (or None)
            }
        """
        from subscriptions.models import UploaderEarnings
        
        # Update download count and revenue
        self.downloads_count += 1
        self.total_revenue += self.price
        
        # Calculate splits
        split = self.get_revenue_split()
        uploader_share = self.price * Decimal(str(split['uploader']))
        app_share = self.price * Decimal(str(split['app']))
        
        # Update earnings
        self.uploader_earnings += uploader_share
        self.platform_earnings += app_share
        self.save()
        
        # Create UploaderEarnings record for tracking (if uploader gets a share)
        earning = None
        if uploader_share > 0:
            earning = UploaderEarnings.objects.create(
                uploader=self.uploader,
                material=self,
                service_type='learning_material',
                gross_amount=self.price,
                platform_commission=app_share,
                net_earnings=uploader_share
            )
        
        # Create or get purchase record
        purchase, created = LearningMaterialPurchase.objects.get_or_create(
            buyer=buyer,
            material=self,
            defaults={'amount_paid': self.price}
        )
        
        if not created:
            # Increment download for existing purchase
            purchase.increment_download()
        
        return {
            'uploader_share': uploader_share,
            'app_share': app_share,
            'purchase': purchase,
            'earning': earning,
        }


class LearningMaterialPurchase(models.Model):
    """
    Record of learning material purchases
    """
    buyer = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='learning_purchases')
    material = models.ForeignKey(LearningMaterial, on_delete=models.CASCADE, related_name='purchases')
    
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    
    # Download tracking
    download_count = models.IntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Learning Material Purchase'
        verbose_name_plural = 'Learning Material Purchases'
        unique_together = ['buyer', 'material']
        # IMPORTANT: Keep existing database table to avoid data migration
        db_table = 'subscriptions_learningmaterialpurchase'
    
    def __str__(self):
        return f"{self.buyer.email} - {self.material.title}"
    
    def increment_download(self):
        """Increment download count"""
        self.download_count += 1
        self.last_downloaded = timezone.now()
        self.save()


class LecturerFollow(models.Model):
    """
    Allow students to follow lecturers for updates on new materials
    Enables student-lecturer connection in Students Hub
    """
    student = models.ForeignKey(
        PolaUser, 
        on_delete=models.CASCADE, 
        related_name='following_lecturers',
        help_text="Student following the lecturer"
    )
    lecturer = models.ForeignKey(
        PolaUser, 
        on_delete=models.CASCADE, 
        related_name='student_followers',
        help_text="Lecturer being followed"
    )
    
    # Engagement
    is_active = models.BooleanField(default=True)
    notifications_enabled = models.BooleanField(
        default=True,
        help_text="Notify student when lecturer uploads new material"
    )
    
    # Timestamps
    followed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'lecturer']
        verbose_name = 'Lecturer Follow'
        verbose_name_plural = 'Lecturer Follows'
        ordering = ['-followed_at']
        indexes = [
            models.Index(fields=['student', '-followed_at']),
            models.Index(fields=['lecturer', '-followed_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} follows {self.lecturer.get_full_name()}"


class MaterialQuestion(models.Model):
    """
    Students can ask questions about specific materials
    Lecturers (or other students) can answer
    Creates direct student-lecturer Q&A interaction
    """
    QUESTION_STATUS = [
        ('open', 'Open'),
        ('answered', 'Answered'),
        ('closed', 'Closed'),
    ]
    
    material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="The material this question is about"
    )
    asker = models.ForeignKey(
        PolaUser,
        on_delete=models.CASCADE,
        related_name='material_questions_asked',
        help_text="Student asking the question"
    )
    
    # Question
    question_text = models.TextField()
    
    # Answer (can be by lecturer or other students)
    answer_text = models.TextField(blank=True)
    answered_by = models.ForeignKey(
        PolaUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='material_questions_answered',
        help_text="Person who answered (lecturer preferred)"
    )
    answered_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=QUESTION_STATUS,
        default='open'
    )
    is_answered_by_uploader = models.BooleanField(
        default=False,
        help_text="True if answered by the material uploader (lecturer)"
    )
    
    # Engagement
    helpful_count = models.IntegerField(
        default=0,
        help_text="How many found this Q&A helpful"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Material Question'
        verbose_name_plural = 'Material Questions'
        indexes = [
            models.Index(fields=['material', 'status', '-created_at']),
            models.Index(fields=['asker', '-created_at']),
            models.Index(fields=['answered_by', '-answered_at']),
        ]
    
    def __str__(self):
        return f"Q: {self.question_text[:50]}... on {self.material.title}"
    
    def mark_as_answered(self, answerer, answer_text):
        """Mark question as answered"""
        self.answer_text = answer_text
        self.answered_by = answerer
        self.answered_at = timezone.now()
        self.status = 'answered'
        
        # Check if answered by material uploader (lecturer)
        self.is_answered_by_uploader = (answerer == self.material.uploader)
        self.save()
        
        return self


class MaterialRating(models.Model):
    """
    Students can rate materials after purchase/download
    Helps identify quality content and good lecturers
    """
    material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    rater = models.ForeignKey(
        PolaUser,
        on_delete=models.CASCADE,
        related_name='material_ratings'
    )
    
    # Rating
    rating = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Rating from 1 (poor) to 5 (excellent)"
    )
    review = models.TextField(
        blank=True,
        help_text="Optional written review"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['material', 'rater']
        verbose_name = 'Material Rating'
        verbose_name_plural = 'Material Ratings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['material', '-created_at']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.rater.get_full_name()} rated {self.material.title}: {self.rating}/5"
