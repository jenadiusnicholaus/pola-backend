"""
Hub Admin - Manage Educational Content Structure & Social Hubs
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    LegalEdTopic, LegalEdSubTopic,
    AdvocatePost, AdvocateDocument, AdvocateComment,
    StudentHubDownload, StudentHubComment
)


@admin.register(LegalEdTopic)
class LegalEdTopicAdmin(admin.ModelAdmin):
    """Admin interface for Topics"""
    list_display = ['name', 'display_order', 'subtopics_count_display', 'materials_count_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'name_sw', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_sw', 'slug', 'display_order')
        }),
        ('Description', {
            'fields': ('description', 'description_sw')
        }),
        ('Appearance', {
            'fields': ('icon',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def subtopics_count_display(self, obj):
        """Display subtopics count"""
        count = obj.get_subtopics_count()
        return format_html('<b>{}</b> subtopics', count)
    subtopics_count_display.short_description = 'Subtopics'
    
    def materials_count_display(self, obj):
        """Display materials count"""
        count = obj.get_materials_count()
        return format_html('<span style="color: #28a745;"><b>{}</b> materials</span>', count)
    materials_count_display.short_description = 'Materials'


@admin.register(LegalEdSubTopic)
class LegalEdSubTopicAdmin(admin.ModelAdmin):
    """Admin interface for Subtopics"""
    list_display = ['name', 'topic', 'display_order', 'materials_count_display', 'is_active', 'created_at']
    list_filter = ['topic', 'is_active', 'created_at']
    search_fields = ['name', 'name_sw', 'description', 'slug', 'topic__name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['topic__display_order', 'display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('topic', 'name', 'name_sw', 'slug', 'display_order')
        }),
        ('Description', {
            'fields': ('description', 'description_sw')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def materials_count_display(self, obj):
        """Display materials count"""
        count = obj.get_materials_count()
        color = '#28a745' if count > 0 else '#dc3545'
        return format_html('<span style="color: {};"><b>{}</b> materials</span>', color, count)
    materials_count_display.short_description = 'Materials'


# ============================================================================
# ADVOCATES HUB ADMIN
# ============================================================================

@admin.register(AdvocatePost)
class AdvocatePostAdmin(admin.ModelAdmin):
    """Admin interface for Advocate Posts"""
    list_display = ['title_display', 'author', 'post_type', 'likes_count', 'comments_count', 'is_pinned', 'created_at']
    list_filter = ['post_type', 'is_pinned', 'is_active', 'created_at']
    search_fields = ['title', 'content', 'author__email', 'author__first_name', 'author__last_name']
    ordering = ['-is_pinned', '-created_at']
    
    def title_display(self, obj):
        return obj.title or obj.content[:50] + "..."
    title_display.short_description = 'Post'


@admin.register(AdvocateDocument)
class AdvocateDocumentAdmin(admin.ModelAdmin):
    """Admin interface for Advocate Documents"""
    list_display = ['title', 'uploader', 'file_type', 'file_size', 'created_at']
    list_filter = ['file_type', 'is_standalone', 'created_at']
    search_fields = ['title', 'description', 'uploader__email']
    ordering = ['-created_at']


@admin.register(AdvocateComment)
class AdvocateCommentAdmin(admin.ModelAdmin):
    """Admin interface for Advocate Comments"""
    list_display = ['author', 'post', 'likes_count', 'is_reply', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__email']
    ordering = ['-created_at']
    
    def is_reply(self, obj):
        return obj.parent_comment is not None
    is_reply.boolean = True


# ============================================================================
# STUDENTS HUB ADMIN
# ============================================================================

# NOTE: Student Hub documents are managed via LearningMaterial in documents app
# These admins only handle Students Hub-specific interactions

@admin.register(StudentHubDownload)
class StudentHubDownloadAdmin(admin.ModelAdmin):
    """Admin interface for tracking downloads in Students Hub"""
    list_display = ['material', 'downloader', 'price_paid', 'download_count', 'created_at', 'last_downloaded_at']
    list_filter = ['created_at', 'last_downloaded_at']
    search_fields = ['material__title', 'downloader__email', 'downloader__first_name', 'downloader__last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'last_downloaded_at']


@admin.register(StudentHubComment)
class StudentHubCommentAdmin(admin.ModelAdmin):
    """Admin interface for Student Hub Comments"""
    list_display = ['author', 'material', 'likes_count', 'is_reply', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__email', 'material__title']
    ordering = ['-created_at']
    
    def is_reply(self, obj):
        return obj.parent_comment is not None
    is_reply.boolean = True
