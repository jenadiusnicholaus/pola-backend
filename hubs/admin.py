"""
Hub Admin - Manage Educational Content Structure & Social Hubs
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    LegalEdTopic, LegalEdSubTopic,
    HubComment, ContentLike, HubCommentLike, ContentBookmark, HubMessage,
    StudentHubDownload, StudentHubComment  # These are deprecated
)
from documents.models import LearningMaterial  # Unified content model


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
# SHARED HUB ADMIN (Advocates, Students, Forums)
# ============================================================================

# HubPost has been replaced by LearningMaterial (documents.models)
# Register LearningMaterial admin in documents/admin.py or subscriptions/admin.py


@admin.register(HubComment)
class HubCommentAdmin(admin.ModelAdmin):
    """Admin interface for Hub Comments (all hubs)"""
    list_display = ['author', 'hub_type', 'content_display', 'likes_count_display', 'is_reply', 'created_at']
    list_filter = ['hub_type', 'is_active', 'created_at']
    search_fields = ['comment_text', 'author__email']
    ordering = ['-created_at']
    
    def content_display(self, obj):
        """Display the content/material title"""
        return obj.content.title if obj.content else "N/A"
    content_display.short_description = 'Content'
    
    def is_reply(self, obj):
        return obj.parent_comment is not None
    is_reply.boolean = True
    
    def likes_count_display(self, obj):
        return obj.get_likes_count()
    likes_count_display.short_description = 'Likes'


@admin.register(ContentLike)
class ContentLikeAdmin(admin.ModelAdmin):
    """Admin interface for Content Likes (unified for all hubs)"""
    list_display = ['user', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'content__title']
    ordering = ['-created_at']


@admin.register(HubCommentLike)
class HubCommentLikeAdmin(admin.ModelAdmin):
    """Admin interface for Comment Likes"""
    list_display = ['user', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    ordering = ['-created_at']


@admin.register(ContentBookmark)
class ContentBookmarkAdmin(admin.ModelAdmin):
    """Admin interface for Content Bookmarks (unified for all hubs)"""
    list_display = ['user', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'content__title']
    ordering = ['-created_at']


@admin.register(HubMessage)
class HubMessageAdmin(admin.ModelAdmin):
    """Admin interface for Private Messages"""
    list_display = ['sender', 'recipient', 'hub_type', 'subject', 'is_read', 'created_at']
    list_filter = ['hub_type', 'is_read', 'created_at']
    search_fields = ['sender__email', 'recipient__email', 'subject', 'message']
    ordering = ['-created_at']


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
    list_display = ['author', 'material', 'likes_count_display', 'is_reply', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content', 'author__email', 'material__title']
    ordering = ['-created_at']
    
    def likes_count_display(self, obj):
        return obj.get_likes_count()
    likes_count_display.short_description = 'Likes'
    
    def is_reply(self, obj):
        return obj.parent_comment is not None
    is_reply.boolean = True
