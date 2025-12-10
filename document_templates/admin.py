from django.contrib import admin
from .models import (
    DocumentTemplate,
    TemplateSection,
    TemplateField,
    UserDocument,
    UserDocumentData
)


class TemplateFieldInline(admin.TabularInline):
    model = TemplateField
    extra = 1
    fields = ['field_name', 'label_en', 'label_sw', 'field_type', 'is_required', 'order']


class TemplateSectionInline(admin.TabularInline):
    model = TemplateSection
    extra = 1
    fields = ['name', 'name_sw', 'order']


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_free', 'price', 'is_active', 'usage_count', 'created_at']
    list_filter = ['category', 'is_free', 'is_active']
    search_fields = ['name', 'name_sw', 'description']
    inlines = [TemplateSectionInline, TemplateFieldInline]
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'name_sw', 'description', 'description_sw', 'category', 'icon')
        }),
        ('Template Content', {
            'fields': ('template_content_en', 'template_content_sw'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('is_free', 'price')
        }),
        ('Status', {
            'fields': ('is_active', 'order', 'usage_count')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TemplateSection)
class TemplateSectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'order']
    list_filter = ['template']
    search_fields = ['name', 'name_sw']


@admin.register(TemplateField)
class TemplateFieldAdmin(admin.ModelAdmin):
    list_display = ['label_en', 'field_name', 'template', 'field_type', 'is_required', 'order']
    list_filter = ['template', 'field_type', 'is_required']
    search_fields = ['field_name', 'label_en', 'label_sw']
    
    fieldsets = (
        ('Field Information', {
            'fields': ('template', 'section', 'field_name', 'field_type', 'is_required', 'order')
        }),
        ('Labels', {
            'fields': ('label_en', 'label_sw', 'placeholder_en', 'placeholder_sw')
        }),
        ('Help Text', {
            'fields': ('help_text_en', 'help_text_sw'),
            'classes': ('collapse',)
        }),
        ('Validation & Options', {
            'fields': ('validation_rules', 'options', 'options_sw', 'default_value'),
            'classes': ('collapse',)
        }),
    )


class UserDocumentDataInline(admin.TabularInline):
    model = UserDocumentData
    extra = 0
    readonly_fields = ['field', 'value']
    can_delete = False


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_title', 'user', 'template', 'language', 'status', 'download_count', 'created_at']
    list_filter = ['template', 'language', 'status', 'is_paid']
    search_fields = ['document_title', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['status', 'generated_file', 'download_count', 'last_downloaded_at', 
                       'generation_started_at', 'generation_completed_at', 'created_at', 'updated_at']
    inlines = [UserDocumentDataInline]
    
    fieldsets = (
        ('Document Information', {
            'fields': ('user', 'template', 'language', 'document_title', 'status')
        }),
        ('Payment', {
            'fields': ('is_paid', 'payment_amount')
        }),
        ('Generated File', {
            'fields': ('generated_file', 'download_count', 'last_downloaded_at')
        }),
        ('Generation Details', {
            'fields': ('generation_started_at', 'generation_completed_at', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserDocumentData)
class UserDocumentDataAdmin(admin.ModelAdmin):
    list_display = ['user_document', 'field', 'value_preview']
    list_filter = ['user_document__template']
    search_fields = ['value', 'user_document__document_title']
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'
