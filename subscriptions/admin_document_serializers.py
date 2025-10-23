"""
Admin Document Management Serializers
Handles learning materials and document pricing
"""

from rest_framework import serializers
from documents.models import LearningMaterial
from .models import PaymentTransaction, UploaderEarnings
from authentication.models import PolaUser
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
from utils.base64_fields import Base64AnyFileField


class UploaderUserSerializer(serializers.ModelSerializer):
    """Nested serializer for uploader details"""
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PolaUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role_name', 'is_active']
        ref_name = 'AdminUploaderUser'
    
    def get_role_name(self, obj):
        """Get user role name"""
        try:
            return obj.user_role.role_name if obj.user_role else None
        except:
            return None


class LearningMaterialAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for learning materials"""
    uploader = UploaderUserSerializer(read_only=True)
    uploader_type = serializers.ChoiceField(
        choices=LearningMaterial.UPLOADER_TYPES,
        required=False,
        help_text="Auto-detected from user role if not provided"
    )
    uploader_type_display = serializers.CharField(source='get_uploader_type_display', read_only=True)
    hub_type_display = serializers.CharField(source='get_hub_type_display', read_only=True)
    language_display = serializers.CharField(source='get_language_display', read_only=True)
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    # Support Base64 file uploads
    file = Base64AnyFileField(
        required=False,
        allow_null=True,
        max_file_size=50 * 1024 * 1024,  # 50MB max for learning materials
        allowed_types=['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'],
        help_text="Upload file as Base64 data URL or multipart file"
    )
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'title', 'description', 'uploader', 'uploader_type', 'uploader_type_display',
            'subtopic', 'hub_type', 'hub_type_display', 'language', 'language_display',
            'content_type', 'content_type_display', 'file', 'file_size', 'file_size_mb',
            'content', 'is_downloadable', 'price',
            'downloads_count', 'views_count', 'is_lecture_material', 'is_verified_quality',
            'is_active', 'is_pinned', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'content': {'required': False},
            'file_size': {'read_only': True},
        }
        ref_name = 'AdminLearningMaterial'
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0
    
    def validate(self, data):
        """Validate that either file or content is provided based on content_type"""
        content_type = data.get('content_type', 'document')
        
        # Document types usually need files
        if content_type in ['document', 'notes', 'past_papers', 'assignments', 'research', 'case_study', 'tutorial', 'other']:
            if not data.get('file') and not self.instance:
                raise serializers.ValidationError({
                    'file': 'File is required for document content types'
                })
        
        # Post types usually need text content
        if content_type in ['discussion', 'question', 'article', 'news', 'announcement']:
            if not data.get('content') and not self.instance:
                raise serializers.ValidationError({
                    'content': 'Text content is required for post content types'
                })
        
        return data
    
    def create(self, validated_data):
        """Handle file size calculation on create"""
        instance = super().create(validated_data)
        
        # Calculate file size if file is provided
        if instance.file:
            try:
                instance.file_size = instance.file.size
                instance.save(update_fields=['file_size'])
            except Exception:
                pass
        
        return instance
    
    def update(self, instance, validated_data):
        """Handle file size calculation on update"""
        instance = super().update(instance, validated_data)
        
        # Recalculate file size if file was updated
        if 'file' in validated_data and instance.file:
            try:
                instance.file_size = instance.file.size
                instance.save(update_fields=['file_size'])
            except Exception:
                pass
        
        return instance


class ApproveMaterialSerializer(serializers.Serializer):
    """Serializer for material approval"""
    is_approved = serializers.BooleanField(required=True)
    admin_note = serializers.CharField(required=False, allow_blank=True)


class UpdateMaterialPriceSerializer(serializers.Serializer):
    """Serializer for updating material price"""
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        min_value=Decimal('0'),
        required=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)


class DocumentStatsSerializer(serializers.Serializer):
    """Serializer for document statistics"""
    # Materials
    total_materials = serializers.IntegerField()
    approved_materials = serializers.IntegerField()
    pending_materials = serializers.IntegerField()
    active_materials = serializers.IntegerField()
    
    # By type
    student_materials = serializers.IntegerField()
    lecturer_materials = serializers.IntegerField()
    admin_materials = serializers.IntegerField()
    
    # Downloads
    total_downloads = serializers.IntegerField()
    paid_downloads = serializers.IntegerField()
    
    # Revenue
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_platform_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_uploader_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Uploaders
    total_uploaders = serializers.IntegerField()
    active_uploaders = serializers.IntegerField()
