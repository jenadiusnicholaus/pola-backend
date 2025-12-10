"""
Document Template System Models

This app manages dynamic document templates where users can:
1. Select from predefined templates (Employment Contract, Notice, etc.)
2. Fill dynamic forms based on template requirements
3. Generate customized documents in English or Swahili
4. Download generated PDFs

Templates include:
- Questionnaire
- Mkataba wa Ajira (Employment Contract)
- Notice
- Resignation Letter
- Fomu ya Kujiungua/Kuacha Kazi (Employment Form)
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from authentication.models import PolaUser
import json


class DocumentTemplate(models.Model):
    """
    Document template definitions
    Each template represents a type of document (e.g., Employment Contract)
    """
    CATEGORY_CHOICES = [
        ('employment', 'Employment Documents'),
        ('legal_notice', 'Legal Notices'),
        ('resignation', 'Resignation Documents'),
        ('questionnaire', 'Questionnaires'),
        ('general', 'General Documents'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name in English")
    name_sw = models.CharField(max_length=200, help_text="Template name in Swahili")
    
    description = models.TextField(help_text="Template description in English")
    description_sw = models.TextField(help_text="Template description in Swahili")
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Template files (HTML templates with placeholders)
    template_content_en = models.TextField(
        help_text="HTML template with {{placeholder}} syntax for English"
    )
    template_content_sw = models.TextField(
        help_text="HTML template with {{placeholder}} syntax for Swahili"
    )
    
    # Pricing
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Price in TZS (0 for free templates)"
    )
    
    # Icon/Image
    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text="Icon name or emoji for template (e.g., 📄, 📝)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")
    
    # Usage stats
    usage_count = models.IntegerField(default=0, help_text="Number of times generated")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        PolaUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Document Template'
        verbose_name_plural = 'Document Templates'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class TemplateSection(models.Model):
    """
    Group template fields into logical sections
    Example: "Employer Information", "Employee Information", "Terms & Conditions"
    """
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    
    name = models.CharField(max_length=200, help_text="Section name in English")
    name_sw = models.CharField(max_length=200, help_text="Section name in Swahili")
    
    description = models.TextField(blank=True, help_text="Section description in English")
    description_sw = models.TextField(blank=True, help_text="Section description in Swahili")
    
    order = models.IntegerField(default=0, help_text="Display order within template")
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Template Section'
        verbose_name_plural = 'Template Sections'
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"


class TemplateField(models.Model):
    """
    Dynamic fields for each template
    Defines what information needs to be collected from users
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Short Text'),
        ('textarea', 'Long Text / Paragraph'),
        ('email', 'Email Address'),
        ('phone', 'Phone Number'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('dropdown', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('signature', 'Signature'),
    ]
    
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    
    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fields',
        help_text="Optional: group field under a section"
    )
    
    # Field identification
    field_name = models.CharField(
        max_length=100,
        help_text="Internal field name (e.g., 'employee_name', 'start_date')"
    )
    
    # Display labels
    label_en = models.CharField(max_length=200, help_text="Field label in English")
    label_sw = models.CharField(max_length=200, help_text="Field label in Swahili")
    
    # Placeholders
    placeholder_en = models.CharField(
        max_length=200,
        blank=True,
        help_text="Placeholder text in English"
    )
    placeholder_sw = models.CharField(
        max_length=200,
        blank=True,
        help_text="Placeholder text in Swahili"
    )
    
    # Help text
    help_text_en = models.TextField(blank=True, help_text="Help text in English")
    help_text_sw = models.TextField(blank=True, help_text="Help text in Swahili")
    
    # Field configuration
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order within section/template")
    
    # Validation rules (stored as JSON)
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON: {min_length: 3, max_length: 100, pattern: '^[A-Z]', etc.}"
    )
    
    # Options for dropdown/radio fields (stored as JSON)
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array for dropdown/radio: ['Option 1', 'Option 2']"
    )
    options_sw = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array for Swahili options"
    )
    
    # Default value
    default_value = models.TextField(blank=True)
    
    class Meta:
        ordering = ['order', 'field_name']
        unique_together = ['template', 'field_name']
        verbose_name = 'Template Field'
        verbose_name_plural = 'Template Fields'
        indexes = [
            models.Index(fields=['template', 'order']),
            models.Index(fields=['section', 'order']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - {self.label_en}"
    
    def get_validation_rules(self):
        """Return validation rules as dict"""
        if isinstance(self.validation_rules, str):
            try:
                return json.loads(self.validation_rules)
            except json.JSONDecodeError:
                return {}
        return self.validation_rules or {}
    
    def get_options(self, language='en'):
        """Get options in specified language"""
        if language == 'sw' and self.options_sw:
            return self.options_sw
        return self.options


class UserDocument(models.Model):
    """
    Generated documents for users
    Tracks document generation history and stores generated files
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Swahili'),
    ]
    
    user = models.ForeignKey(
        PolaUser,
        on_delete=models.CASCADE,
        related_name='generated_documents'
    )
    
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name='user_documents'
    )
    
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Generated file
    generated_file = models.FileField(
        upload_to='generated_documents/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Document metadata
    document_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Custom title given by user"
    )
    
    # Payment tracking (for premium templates)
    is_paid = models.BooleanField(default=False)
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Generation details
    generation_started_at = models.DateTimeField(null=True, blank=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Download tracking
    download_count = models.IntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Document'
        verbose_name_plural = 'User Documents'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['template', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        title = self.document_title or self.template.name
        return f"{self.user.get_full_name()} - {title}"
    
    def mark_as_generating(self):
        """Mark document as being generated"""
        self.status = 'generating'
        self.generation_started_at = timezone.now()
        self.save(update_fields=['status', 'generation_started_at', 'updated_at'])
    
    def mark_as_completed(self):
        """Mark document as completed"""
        self.status = 'completed'
        self.generation_completed_at = timezone.now()
        self.save(update_fields=['status', 'generation_completed_at', 'updated_at'])
    
    def mark_as_failed(self, error_message):
        """Mark document generation as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])
    
    def increment_download(self):
        """Increment download counter"""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded_at'])


class UserDocumentData(models.Model):
    """
    Stores user's filled data for each field in the document
    One record per field per document
    """
    user_document = models.ForeignKey(
        UserDocument,
        on_delete=models.CASCADE,
        related_name='field_data'
    )
    
    field = models.ForeignKey(
        TemplateField,
        on_delete=models.CASCADE,
        related_name='user_data'
    )
    
    value = models.TextField(help_text="User's input for this field")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user_document', 'field']
        verbose_name = 'User Document Data'
        verbose_name_plural = 'User Document Data'
        indexes = [
            models.Index(fields=['user_document', 'field']),
        ]
    
    def __str__(self):
        return f"{self.user_document} - {self.field.field_name}: {self.value[:50]}"
