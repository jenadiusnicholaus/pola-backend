"""
Admin Document Management Serializers
Handles learning materials and document pricing
"""

from rest_framework import serializers
from .models import LearningMaterial, PaymentTransaction, UploaderEarnings
from authentication.models import PolaUser
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal


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
    uploader_type_display = serializers.CharField(source='get_uploader_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'title', 'description', 'uploader', 'uploader_type', 'uploader_type_display',
            'category', 'category_display', 'file', 'file_size', 'file_size_mb', 'price',
            'downloads_count', 'total_revenue', 'uploader_earnings',
            'is_active', 'is_approved', 'created_at', 'updated_at'
        ]
        ref_name = 'AdminLearningMaterial'
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


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
