"""
Document Template Serializers
"""
from rest_framework import serializers
from .models import (
    DocumentTemplate,
    TemplateSection,
    TemplateField,
    UserDocument,
    UserDocumentData
)


class TemplateFieldSerializer(serializers.ModelSerializer):
    """Serializer for template fields"""
    
    class Meta:
        model = TemplateField
        fields = [
            'id', 'field_name', 'label_en', 'label_sw',
            'placeholder_en', 'placeholder_sw',
            'help_text_en', 'help_text_sw',
            'field_type', 'is_required', 'order',
            'validation_rules', 'options', 'options_sw',
            'default_value'
        ]


class TemplateSectionSerializer(serializers.ModelSerializer):
    """Serializer for template sections with nested fields"""
    fields = TemplateFieldSerializer(many=True, read_only=True)
    
    class Meta:
        model = TemplateSection
        fields = [
            'id', 'name', 'name_sw', 'description',
            'description_sw', 'order', 'fields'
        ]


class DocumentTemplateListSerializer(serializers.ModelSerializer):
    """Serializer for template list view"""
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'name_sw', 'description',
            'description_sw', 'category', 'is_free',
            'price', 'icon', 'usage_count'
        ]


class DocumentTemplateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with sections and fields"""
    sections = TemplateSectionSerializer(many=True, read_only=True)
    fields_without_section = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'name_sw', 'description',
            'description_sw', 'category', 'is_free',
            'price', 'icon', 'usage_count',
            'sections', 'fields_without_section'
        ]
    
    def get_fields_without_section(self, obj):
        """Get fields that don't belong to any section"""
        fields = obj.fields.filter(section__isnull=True)
        return TemplateFieldSerializer(fields, many=True).data


class UserDocumentDataSerializer(serializers.ModelSerializer):
    """Serializer for user document data"""
    field_name = serializers.CharField(source='field.field_name', read_only=True)
    field_label_en = serializers.CharField(source='field.label_en', read_only=True)
    field_label_sw = serializers.CharField(source='field.label_sw', read_only=True)
    
    class Meta:
        model = UserDocumentData
        fields = ['id', 'field', 'field_name', 'field_label_en', 'field_label_sw', 'value']


class UserDocumentSerializer(serializers.ModelSerializer):
    """Serializer for user documents"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_name_sw = serializers.CharField(source='template.name_sw', read_only=True)
    field_data = UserDocumentDataSerializer(many=True, read_only=True)
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDocument
        fields = [
            'id', 'template', 'template_name', 'template_name_sw',
            'language', 'status', 'document_title',
            'generated_file', 'download_url',
            'is_paid', 'payment_amount',
            'download_count', 'last_downloaded_at',
            'field_data', 'created_at', 'updated_at',
            'error_message'
        ]
        read_only_fields = ['generated_file', 'status', 'download_count']
    
    def get_download_url(self, obj):
        """Get download URL if file exists"""
        if obj.generated_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.generated_file.url)
        return None


class GenerateDocumentSerializer(serializers.Serializer):
    """Serializer for document generation request"""
    template_id = serializers.IntegerField(required=True)
    language = serializers.ChoiceField(choices=['en', 'sw'], default='en')
    document_title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    data = serializers.JSONField(required=True, help_text="Field data as {field_name: value}")
    
    def validate_template_id(self, value):
        """Validate template exists and is active"""
        try:
            template = DocumentTemplate.objects.get(id=value, is_active=True)
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found or inactive")
        return value
    
    def validate_data(self, value):
        """Validate that data is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Data must be a JSON object")
        return value


class ValidateDocumentDataSerializer(serializers.Serializer):
    """Serializer for validating document data before generation"""
    template_id = serializers.IntegerField(required=True)
    language = serializers.ChoiceField(choices=['en', 'sw'], default='en')
    data = serializers.JSONField(required=True)
    
    def validate_template_id(self, value):
        """Validate template exists"""
        try:
            DocumentTemplate.objects.get(id=value, is_active=True)
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found")
        return value
