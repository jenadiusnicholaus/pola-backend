"""
Document Template Serializers
"""
from rest_framework import serializers
from .models import (
    DocumentTemplate,
    TemplateSection,
    TemplateField,
    UserDocument,
    UserDocumentData,
    DocumentContent
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
    all_fields = serializers.SerializerMethodField()  # Renamed from 'fields'
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'name_sw', 'description',
            'description_sw', 'category', 'is_free',
            'price', 'icon', 'usage_count',
            'sections', 'fields_without_section', 'all_fields'
        ]
    
    def get_fields_without_section(self, obj):
        """Get fields that don't belong to any section"""
        fields = obj.fields.filter(section__isnull=True)
        return TemplateFieldSerializer(fields, many=True).data
    
    def get_all_fields(self, obj):
        """Get all fields for this template"""
        all_fields = obj.fields.all().order_by('order')
        return TemplateFieldSerializer(all_fields, many=True).data


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
    can_download = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDocument
        fields = [
            'id', 'template', 'template_name', 'template_name_sw',
            'language', 'status', 'document_title',
            'generated_file', 'download_url',
            'is_paid', 'payment_amount',
            'download_count', 'last_downloaded_at',
            'field_data', 'created_at', 'updated_at',
            'error_message', 'can_download'
        ]
        read_only_fields = ['generated_file', 'status', 'download_count']
    
    def get_download_url(self, obj):
        """Get download URL if file exists"""
        if obj.generated_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.generated_file.url)
        return None
    
    def get_can_download(self, obj):
        """Check if user can download (free template or paid)"""
        # Free templates can always be downloaded
        if obj.template.is_free or obj.template.price == 0:
            return True
        # Paid documents need payment
        return obj.is_paid


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


class DocumentContentListSerializer(serializers.ModelSerializer):
    """Serializer for document content list view"""

    class Meta:
        model = DocumentContent
        fields = [
            'id', 'title', 'title_sw', 'slug', 'category',
            'is_active', 'is_public', 'display_order',
            'created_at', 'updated_at'
        ]


class DocumentContentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for document content"""

    class Meta:
        model = DocumentContent
        fields = [
            'id', 'title', 'title_sw', 'slug', 'category',
            'content', 'content_sw', 'is_active', 'is_public',
            'display_order', 'created_at', 'updated_at'
        ]


class DocumentContentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating document content"""
    slug = serializers.SlugField(required=False, allow_blank=True, help_text="Auto-generated from title if not provided")

    class Meta:
        model = DocumentContent
        fields = [
            'id', 'title', 'title_sw', 'slug', 'category',
            'content', 'content_sw', 'is_active', 'is_public',
            'display_order'
        ]
        extra_kwargs = {
            'slug': {'required': False, 'allow_blank': True}
        }

    def validate_slug(self, value):
        """Ensure slug is unique if provided"""
        if not value:
            return value
        instance_id = self.instance.id if self.instance else None
        if DocumentContent.objects.filter(slug=value).exclude(id=instance_id).exists():
            raise serializers.ValidationError("A document with this slug already exists.")
        return value

    def create(self, validated_data):
        """Auto-generate slug from title if not provided"""
        from django.utils.text import slugify

        if not validated_data.get('slug'):
            base_slug = slugify(validated_data['title'])
            slug = base_slug
            counter = 1

            while DocumentContent.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            validated_data['slug'] = slug

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Auto-generate slug from title if not provided and title changed"""
        from django.utils.text import slugify

        if not validated_data.get('slug') and validated_data.get('title') != instance.title:
            base_slug = slugify(validated_data['title'])
            slug = base_slug
            counter = 1

            while DocumentContent.objects.filter(slug=slug).exclude(id=instance.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            validated_data['slug'] = slug

        return super().update(instance, validated_data)
