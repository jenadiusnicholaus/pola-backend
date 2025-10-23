from django.contrib import admin
from .models import (
    LecturerFollow,
    MaterialQuestion,
    MaterialRating,
)

# NOTE: LearningMaterial and LearningMaterialPurchase are registered in subscriptions/admin.py


@admin.register(LecturerFollow)
class LecturerFollowAdmin(admin.ModelAdmin):
    """Admin for student-lecturer follows"""
    list_display = ['student', 'lecturer', 'is_active', 'notifications_enabled', 'followed_at']
    list_filter = ['is_active', 'notifications_enabled', 'followed_at']
    search_fields = [
        'student__email', 'student__first_name', 'student__last_name',
        'lecturer__email', 'lecturer__first_name', 'lecturer__last_name'
    ]
    ordering = ['-followed_at']
    readonly_fields = ['followed_at']


@admin.register(MaterialQuestion)
class MaterialQuestionAdmin(admin.ModelAdmin):
    """Admin for Q&A on materials"""
    list_display = [
        'get_question_preview', 'asker', 'material', 'status',
        'is_answered_by_uploader', 'answered_by', 'helpful_count', 'created_at'
    ]
    list_filter = ['status', 'is_answered_by_uploader', 'created_at', 'answered_at']
    search_fields = [
        'question_text', 'answer_text', 
        'asker__email', 'asker__first_name', 'asker__last_name',
        'answered_by__email', 'answered_by__first_name', 'answered_by__last_name',
        'material__title'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'answered_at', 'helpful_count']
    
    fieldsets = (
        ('Question', {
            'fields': ('material', 'asker', 'question_text', 'status')
        }),
        ('Answer', {
            'fields': ('answer_text', 'answered_by', 'answered_at', 'is_answered_by_uploader')
        }),
        ('Engagement', {
            'fields': ('helpful_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_question_preview(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    get_question_preview.short_description = 'Question'


@admin.register(MaterialRating)
class MaterialRatingAdmin(admin.ModelAdmin):
    """Admin for material ratings"""
    list_display = ['rater', 'material', 'rating', 'created_at', 'get_review_preview']
    list_filter = ['rating', 'created_at']
    search_fields = [
        'rater__email', 'rater__first_name', 'rater__last_name',
        'material__title', 'review'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_review_preview(self, obj):
        if obj.review:
            return obj.review[:50] + "..." if len(obj.review) > 50 else obj.review
        return "(No review)"
    get_review_preview.short_description = 'Review'
