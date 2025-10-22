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
    Learning materials uploaded by students, lecturers, or admins
    
    Used by:
    - Legal Education Hub (admin-uploaded hub content)
    - Students Hub (student/lecturer document marketplace)
    """
    UPLOADER_TYPES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Admin'),
    ]
    
    CATEGORY_CHOICES = [
        ('notes', 'Study Notes'),
        ('past_papers', 'Past Exam Papers'),
        ('assignments', 'Assignments'),
        ('tutorials', 'Tutorials'),
        ('hub_content', 'Hub Content'),
        ('other', 'Other'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('file', 'File (PDF, DOC, etc)'),
        ('rich_text', 'Rich Text/HTML'),
    ]
    
    uploader = models.ForeignKey(PolaUser, on_delete=models.CASCADE, related_name='uploaded_materials')
    uploader_type = models.CharField(max_length=20, choices=UPLOADER_TYPES)
    
    # Hub relationship (optional - for hub-organized content)
    subtopic = models.ForeignKey(
        'hubs.LegalEdSubTopic', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='materials',
        help_text="Link to hub subtopic"
    )
    
    # Material details
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en', help_text="Content language")
    
    # Content (can be file or rich text)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='file')
    file = models.FileField(upload_to='learning_materials/', blank=True, null=True, help_text="File content (PDF, DOC, etc)")
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    rich_text_content = models.TextField(blank=True, help_text="Rich text/HTML content")
    
    # Download settings
    is_downloadable = models.BooleanField(default=True, help_text="Allow users to download this material")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Stats
    downloads_count = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    uploader_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    
    is_approved = models.BooleanField(default=False, help_text="Admin approval required")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Learning Material'
        verbose_name_plural = 'Learning Materials'
        # IMPORTANT: Keep existing database table to avoid data migration
        db_table = 'subscriptions_learningmaterial'
    
    def __str__(self):
        return f"{self.title} by {self.uploader.email}"
    
    def get_revenue_split(self):
        """
        Calculate revenue split based on uploader type
        
        Student uploads: 50/50 (App/Uploader)
        Lecturer uploads: 40/60 (App/Uploader) - Lecturer gets 60%
        Admin uploads: 100/0 (App/Uploader) - All to platform
        """
        splits = {
            'student': {'uploader': 0.50, 'app': 0.50},   # 50/50
            'lecturer': {'uploader': 0.60, 'app': 0.40},  # 60% uploader, 40% app
            'admin': {'uploader': 0.00, 'app': 1.00},     # 100% to app
        }
        return splits.get(self.uploader_type, {'uploader': 0.50, 'app': 0.50})
    
    def record_purchase(self, buyer):
        """Record a purchase and distribute revenue"""
        # Late import to avoid circular dependency
        from subscriptions.models import UploaderEarnings
        
        self.downloads_count += 1
        self.total_revenue += self.price
        
        # Calculate revenue split
        split = self.get_revenue_split()
        uploader_share = self.price * Decimal(str(split['uploader']))
        app_share = self.price * Decimal(str(split['app']))
        
        self.uploader_earnings += uploader_share
        self.save()
        
        # Record in UploaderEarnings
        if uploader_share > 0:
            UploaderEarnings.objects.create(
                uploader=self.uploader,
                material=self,
                service_type='learning_material',
                gross_amount=self.price,
                platform_commission=app_share,
                net_earnings=uploader_share
            )
        
        return {
            'uploader_share': uploader_share,
            'app_share': app_share
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
