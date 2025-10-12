"""
Verification Serializers
Handles serialization for documents and verification processes
"""

from rest_framework import serializers
from .models import Document, Verification, VerificationDocument, PolaUser


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'document_type', 'document_type_display',
            'file', 'file_url', 'title', 'description',
            'verification_status', 'verification_status_display',
            'verified_by', 'verified_by_name',
            'verification_date', 'verification_notes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'verification_status', 'verified_by',
            'verification_date', 'verification_notes', 'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return f"{obj.verified_by.first_name} {obj.verified_by.last_name}"
        return None

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading documents"""
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'title', 'description']

    def validate_file(self, value):
        """Validate file size and type"""
        # Max file size: 10MB
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Allowed file types
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only PDF, JPG, PNG, and DOC/DOCX files are allowed"
            )
        
        return value


class VerificationSerializer(serializers.ModelSerializer):
    """Serializer for Verification model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_step_display = serializers.CharField(source='get_current_step_display', read_only=True)
    verified_by_name = serializers.SerializerMethodField()
    progress = serializers.FloatField(source='verification_progress', read_only=True)
    documents = serializers.SerializerMethodField()
    required_documents = serializers.SerializerMethodField()

    class Meta:
        model = Verification
        fields = [
            'id', 'user', 'user_email', 'user_name', 'user_role',
            'status', 'status_display',
            'current_step', 'current_step_display',
            'verified_by', 'verified_by_name',
            'verification_date', 'rejection_reason',
            'verification_notes', 'progress',
            'documents', 'required_documents',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'verified_by', 'verification_date',
            'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_user_role(self, obj):
        if obj.user.user_role:
            return {
                'id': obj.user.user_role.id,
                'name': obj.user.user_role.role_name,
                'display': obj.user.user_role.get_role_name_display()
            }
        return None

    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return f"{obj.verified_by.first_name} {obj.verified_by.last_name}"
        return None

    def get_documents(self, obj):
        """Get all documents uploaded by the user"""
        documents = Document.objects.filter(user=obj.user)
        return DocumentSerializer(documents, many=True, context=self.context).data

    def get_required_documents(self, obj):
        """Get required documents for this user's role"""
        role_name = obj.user.user_role.role_name if obj.user.user_role else None
        
        requirements = {
            'advocate': [
                {'type': 'roll_number_cert', 'label': 'Roll Number Certificate', 'required': True},
                {'type': 'practice_license', 'label': 'Practice License', 'required': True},
                {'type': 'work_certificate', 'label': 'Certificate of Work', 'required': True}
            ],
            'lawyer': [
                {'type': 'professional_cert', 'label': 'Professional Certificate', 'required': True},
                {'type': 'employment_letter', 'label': 'Employment Letter', 'required': True},
                {'type': 'organization_cert', 'label': 'Organization Certificate', 'required': False}
            ],
            'paralegal': [
                {'type': 'professional_cert', 'label': 'Professional Certificate', 'required': True},
                {'type': 'employment_letter', 'label': 'Employment Letter', 'required': True},
                {'type': 'organization_cert', 'label': 'Organization Certificate', 'required': False}
            ],
            'law_firm': [
                {'type': 'business_license', 'label': 'Business License', 'required': True},
                {'type': 'registration_cert', 'label': 'Registration Certificate', 'required': True},
                {'type': 'firm_documents', 'label': 'Other Firm Documents', 'required': False}
            ],
            'law_student': [],  # Auto-verified
            'citizen': []  # Auto-verified
        }
        
        required = requirements.get(role_name, [])
        
        # Add upload status for each required document
        user_docs = Document.objects.filter(user=obj.user)
        for req in required:
            doc = user_docs.filter(document_type=req['type']).first()
            if doc:
                req['uploaded'] = True
                req['status'] = doc.verification_status
                req['document_id'] = doc.id
            else:
                req['uploaded'] = False
                req['status'] = None
                req['document_id'] = None
        
        return required


class VerificationActionSerializer(serializers.Serializer):
    """Serializer for verification actions (approve/reject)"""
    status = serializers.ChoiceField(
        choices=['verified', 'rejected'],
        required=False,
        default='verified'
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class UserVerificationStatusSerializer(serializers.ModelSerializer):
    """Simplified serializer for user verification status"""
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = PolaUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_verified', 'verification_status']
        read_only_fields = fields

    def get_verification_status(self, obj):
        try:
            verification = obj.verification
            return {
                'status': verification.status,
                'status_display': verification.get_status_display(),
                'progress': verification.verification_progress,
                'current_step': verification.current_step,
                'current_step_display': verification.get_current_step_display()
            }
        except Verification.DoesNotExist:
            return None
