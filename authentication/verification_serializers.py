"""
Verification Serializers
Handles serialization for documents and verification processes
"""

from rest_framework import serializers
from .models import Document, Verification, VerificationDocument, PolaUser
from utils.base64_fields import Base64AnyFileField


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
    verified_by_id = serializers.IntegerField(source='verified_by.id', read_only=True, allow_null=True)
    verified_by_name = serializers.SerializerMethodField()
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    is_image = serializers.SerializerMethodField()
    is_pdf = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'user_id', 'user_email', 'user_name', 'user_full_name',
            'document_type', 'document_type_display',
            'file', 'file_url', 'file_type', 'file_extension', 'file_size',
            'is_image', 'is_pdf', 'preview_url',
            'title', 'description',
            'verification_status', 'verification_status_display',
            'verified_by_id', 'verified_by_name',
            'verification_date', 'verification_notes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_id', 'verification_status', 'verified_by_id',
            'verification_date', 'verification_notes', 'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_user_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

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

    def get_file_type(self, obj):
        """Get the MIME type of the file"""
        if obj.file:
            import mimetypes
            file_path = obj.file.name
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'
        return None

    def get_file_extension(self, obj):
        """Get file extension (e.g., 'pdf', 'jpg', 'png')"""
        if obj.file:
            import os
            _, ext = os.path.splitext(obj.file.name)
            return ext.lower().lstrip('.')
        return None

    def get_file_size(self, obj):
        """Get file size in bytes"""
        if obj.file:
            try:
                return obj.file.size
            except Exception:
                return None
        return None

    def get_is_image(self, obj):
        """Check if file is an image (jpg, jpeg, png, gif, etc.)"""
        if obj.file:
            import os
            _, ext = os.path.splitext(obj.file.name)
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
            return ext.lower() in image_extensions
        return False

    def get_is_pdf(self, obj):
        """Check if file is a PDF"""
        if obj.file:
            import os
            _, ext = os.path.splitext(obj.file.name)
            return ext.lower() == '.pdf'
        return False

    def get_preview_url(self, obj):
        """Get preview URL (same as file_url for now, frontend can handle different viewers)"""
        return self.get_file_url(obj)


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading documents with base64 support"""
    file = Base64AnyFileField(required=True)
    
    class Meta:
        model = Document
        fields = ['document_type', 'file', 'title', 'description']

    def validate(self, data):
        """Validate document submission to prevent duplicates and ensure proper sizing"""
        user = self.context['request'].user
        document_type = data.get('document_type')
        
        # Set document_type on file field for size validation
        if 'file' in data and document_type:
            self.fields['file'].document_type = document_type
        
        # Check for duplicate document type
        existing_document = Document.objects.filter(
            user=user,
            document_type=document_type,
            is_active=True
        ).first()
        
        if existing_document:
            raise serializers.ValidationError({
                'document_type': f'You have already submitted a {existing_document.get_document_type_display()}. '
                               f'Please update the existing document instead of creating a new one. '
                               f'Existing document ID: {existing_document.id}'
            })
        
        return data

    def validate_file(self, value):
        """Additional file validation if needed"""
        if value is None:
            raise serializers.ValidationError("File is required")
        return value


class VerificationSerializer(serializers.ModelSerializer):
    """Serializer for Verification model"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    user_full_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    user_address = serializers.SerializerMethodField()
    user_date_of_birth = serializers.DateField(source='user.date_of_birth', read_only=True)
    user_gender = serializers.CharField(source='user.gender', read_only=True)
    user_nationality = serializers.CharField(source='user.nationality', read_only=True)
    profile_picture = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_step_display = serializers.CharField(source='get_current_step_display', read_only=True)
    verified_by_id = serializers.IntegerField(source='verified_by.id', read_only=True, allow_null=True)
    verified_by_name = serializers.SerializerMethodField()
    progress = serializers.FloatField(source='verification_progress', read_only=True)
    documents = serializers.SerializerMethodField()
    required_documents = serializers.SerializerMethodField()
    documents_summary = serializers.SerializerMethodField()
    missing_information = serializers.SerializerMethodField()
    days_since_registration = serializers.SerializerMethodField()
    
    def get_profile_picture(self, obj):
        """Get user's profile picture relative path"""
        if obj.user.profile_picture:
            return obj.user.profile_picture.name
        return None
    
    def get_profile_picture_url(self, obj):
        """Get full URL for user's profile picture"""
        if obj.user.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile_picture.url)
            return obj.user.profile_picture.url
        return None

    class Meta:
        model = Verification
        fields = [
            'id', 'user_id', 'user_email', 'user_name', 'user_full_name', 'user_role',
            'user_phone', 'user_address', 'user_date_of_birth', 
            'user_gender', 'user_nationality', 'profile_picture', 'profile_picture_url',
            'status', 'status_display',
            'current_step', 'current_step_display',
            'verified_by_id', 'verified_by_name',
            'verification_date', 'rejection_reason',
            'verification_notes', 'progress',
            'documents', 'required_documents', 'documents_summary',
            'missing_information',
            'days_since_registration',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_id', 'verified_by_id', 'verification_date',
            'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_user_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

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

    def get_user_phone(self, obj):
        """Get user's phone number from contact info"""
        try:
            return obj.user.contact.phone_number if hasattr(obj.user, 'contact') else None
        except:
            return None

    def get_user_address(self, obj):
        """Get user's address information as structured object"""
        try:
            if hasattr(obj.user, 'address') and obj.user.address:
                return {
                    'office_address': obj.user.address.office_address or None,
                    'ward': obj.user.address.ward or None,
                    'district': str(obj.user.address.district) if obj.user.address.district else None,
                    'region': str(obj.user.address.region) if obj.user.address.region else None
                }
        except Exception as e:
            pass
        return None

    def get_documents_summary(self, obj):
        """Get summary of uploaded documents"""
        documents = Document.objects.filter(user=obj.user, is_active=True)
        return {
            'total_uploaded': documents.count(),
            'verified': documents.filter(verification_status='verified').count(),
            'pending': documents.filter(verification_status='pending').count(),
            'rejected': documents.filter(verification_status='rejected').count(),
            'latest_upload': documents.order_by('-created_at').first().created_at if documents.exists() else None
        }

    def get_days_since_registration(self, obj):
        """Calculate days since user registration"""
        from django.utils import timezone
        if obj.user.date_joined:
            delta = timezone.now().date() - obj.user.date_joined.date()
            return delta.days
        return None

    def get_documents(self, obj):
        """Get all active documents uploaded by the user"""
        documents = Document.objects.filter(user=obj.user, is_active=True)
        # Debug: Log the query results
        print(f"DEBUG: User {obj.user.id} ({obj.user.email}) has {documents.count()} active documents")
        for doc in documents:
            print(f"  - Document {doc.id}: {doc.document_type} ({doc.verification_status})")
        return DocumentSerializer(documents, many=True, context=self.context).data

    def get_missing_information(self, obj):
        """
        Analyze and return what information is missing for verification
        Organized by verification steps for better admin workflow
        """
        role_name = obj.user.user_role.role_name if obj.user.user_role else None
        user = obj.user
        
        # Auto-verified roles have no missing information
        auto_verify_roles = ['citizen', 'law_student', 'lecturer']
        if role_name in auto_verify_roles:
            return {
                'has_missing_items': False,
                'is_ready_for_approval': True,
                'by_step': {
                    'documents': {'status': 'not_required', 'issues': []},
                    'identity': {'status': 'not_required', 'issues': []},
                    'contact': {'status': 'not_required', 'issues': []},
                    'role_specific': {'status': 'not_required', 'issues': []},
                    'final': {'status': 'complete', 'issues': []}
                },
                'summary': 'Auto-verified role - no verification requirements'
            }
        
        # Initialize step-based structure
        by_step = {
            'documents': {
                'status': 'incomplete',  # incomplete, pending_review, complete
                'is_current': obj.current_step == 'documents',
                'issues': [],
                'required_fields': [],
                'verified_fields': []
            },
            'identity': {
                'status': 'incomplete',
                'is_current': obj.current_step == 'identity',
                'issues': [],
                'required_fields': [] if role_name == 'law_firm' else ['first_name', 'last_name', 'date_of_birth', 'gender'],
                'verified_fields': []
            },
            'contact': {
                'status': 'incomplete',
                'is_current': obj.current_step == 'contact',
                'issues': [],
                'required_fields': ['phone_number', 'email', 'contact_address'],
                'verified_fields': []
            },
            'role_specific': {
                'status': 'incomplete',
                'is_current': obj.current_step == 'role_specific',
                'issues': [],
                'required_fields': [],
                'verified_fields': []
            },
            'final': {
                'status': 'incomplete',
                'is_current': obj.current_step == 'final',
                'issues': [],
                'required_fields': [],
                'verified_fields': []
            }
        }
        
        # Set role-specific required_fields based on user role
        if role_name == 'advocate':
            by_step['role_specific']['required_fields'] = ['roll_number', 'regional_chapter']
        elif role_name in ['lawyer', 'paralegal']:
            by_step['role_specific']['required_fields'] = ['place_of_work']
        elif role_name == 'law_firm':
            by_step['role_specific']['required_fields'] = ['firm_name', 'managing_partner']
        
        # STEP 1: DOCUMENTS
        required_docs_info = self.get_required_documents(obj)
        docs_complete = True
        docs_pending = False
        
        for doc_info in required_docs_info:
            if doc_info['required']:
                if not doc_info['uploaded']:
                    by_step['documents']['issues'].append({
                        'type': 'missing_document',
                        'document_type': doc_info['type'],
                        'label': doc_info['label'],
                        'message': f"{doc_info['label']} not uploaded"
                    })
                    docs_complete = False
                elif doc_info['status'] == 'pending':
                    by_step['documents']['issues'].append({
                        'type': 'pending_document',
                        'document_type': doc_info['type'],
                        'label': doc_info['label'],
                        'document_id': doc_info['document_id'],
                        'message': f"{doc_info['label']} awaiting admin review"
                    })
                    docs_complete = False
                    docs_pending = True
                elif doc_info['status'] == 'rejected':
                    by_step['documents']['issues'].append({
                        'type': 'rejected_document',
                        'document_type': doc_info['type'],
                        'label': doc_info['label'],
                        'document_id': doc_info['document_id'],
                        'message': f"{doc_info['label']} was rejected - needs re-upload"
                    })
                    docs_complete = False
                elif doc_info['status'] == 'approved':
                    # Track approved documents
                    by_step['documents']['verified_fields'].append({
                        'field': doc_info['type'],
                        'label': doc_info['label'],
                        'value': f"Document #{doc_info['document_id']}",
                        'status': 'verified',
                        'document_id': doc_info['document_id']
                    })
        
        # Set documents step status
        if docs_complete and not by_step['documents']['issues']:
            by_step['documents']['status'] = 'complete'
        elif docs_pending:
            by_step['documents']['status'] = 'pending_review'
        else:
            by_step['documents']['status'] = 'incomplete'
        
        # STEP 2: IDENTITY
        # Law firms skip individual identity verification as they are organizations
        if role_name == 'law_firm':
            by_step['identity']['status'] = 'complete'
            by_step['identity']['verified_fields'].append({
                'field': 'organization_type',
                'label': 'Organization Type',
                'value': 'Law Firm',
                'status': 'verified'
            })
        else:
            # Track what's verified for individual users
            if user.first_name and user.last_name:
                by_step['identity']['verified_fields'].append({
                    'field': 'full_name',
                    'label': 'Full Name',
                    'value': f"{user.first_name} {user.last_name}",
                    'status': 'verified'
                })
            else:
                by_step['identity']['issues'].append({
                    'type': 'missing_field',
                    'field': 'full_name',
                    'message': 'Full name is incomplete'
                })
            
            if user.date_of_birth:
                by_step['identity']['verified_fields'].append({
                    'field': 'date_of_birth',
                    'label': 'Date of Birth',
                    'value': str(user.date_of_birth),
                    'status': 'verified'
                })
            else:
                by_step['identity']['issues'].append({
                    'type': 'missing_field',
                    'field': 'date_of_birth',
                    'message': 'Date of birth is missing'
                })
            
            if user.gender:
                by_step['identity']['verified_fields'].append({
                    'field': 'gender',
                    'label': 'Gender',
                    'value': user.get_gender_display() if hasattr(user, 'get_gender_display') else user.gender,
                    'status': 'verified'
                })
            else:
                by_step['identity']['issues'].append({
                    'type': 'missing_field',
                    'field': 'gender',
                    'message': 'Gender is not specified'
                })
            
            if not by_step['identity']['issues']:
                by_step['identity']['status'] = 'complete'
        
        # STEP 3: CONTACT
        # Track phone number
        if hasattr(user, 'contact') and user.contact and user.contact.phone_number:
            by_step['contact']['verified_fields'].append({
                'field': 'phone_number',
                'label': 'Phone Number',
                'value': user.contact.phone_number,
                'status': 'verified'
            })
        else:
            by_step['contact']['issues'].append({
                'type': 'missing_field',
                'field': 'phone_number',
                'message': 'Phone number is missing'
            })
        
        # Track email (from user model)
        if user.email:
            by_step['contact']['verified_fields'].append({
                'field': 'email',
                'label': 'Email',
                'value': user.email,
                'status': 'verified'
            })
        else:
            by_step['contact']['issues'].append({
                'type': 'missing_field',
                'field': 'email',
                'message': 'Email is missing'
            })
        
        # Track address - MANDATORY, return as object
        if hasattr(user, 'address') and user.address:
            address_obj = {
                'office_address': user.address.office_address or None,
                'ward': user.address.ward or None,
                'district': str(user.address.district) if user.address.district else None,
                'region': str(user.address.region) if user.address.region else None
            }
            by_step['contact']['verified_fields'].append({
                'field': 'contact_address',
                'label': 'Contact Address',
                'value': address_obj,
                'status': 'verified'
            })
        else:
            by_step['contact']['issues'].append({
                'type': 'missing_field',
                'field': 'contact_address',
                'message': 'Address information is missing'
            })
        
        if not by_step['contact']['issues']:
            by_step['contact']['status'] = 'complete'
        
        # STEP 4: ROLE-SPECIFIC
        if role_name == 'advocate':
            if user.roll_number:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'roll_number',
                    'label': 'Roll Number',
                    'value': user.roll_number,
                    'status': 'verified'
                })
            else:
                by_step['role_specific']['issues'].append({
                    'type': 'missing_field',
                    'field': 'roll_number',
                    'message': 'Roll number is missing'
                })
            
            # Regional chapter for advocates (TLS chapter)
            if user.regional_chapter:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'regional_chapter',
                    'label': 'Regional Chapter',
                    'value': str(user.regional_chapter),
                    'status': 'verified'
                })
            else:
                by_step['role_specific']['issues'].append({
                    'type': 'missing_field',
                    'field': 'regional_chapter',
                    'message': 'Regional chapter not specified'
                })
            
            # Years of experience is optional for advocates - only add if provided
            if user.years_of_experience:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'years_of_experience',
                    'label': 'Years of Experience (Optional)',
                    'value': str(user.years_of_experience),
                    'status': 'verified'
                })
        
        elif role_name in ['lawyer', 'paralegal']:
            if user.place_of_work:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'place_of_work',
                    'label': 'Place of Work',
                    'value': str(user.place_of_work),
                    'status': 'verified'
                })
            else:
                by_step['role_specific']['issues'].append({
                    'type': 'missing_field',
                    'field': 'place_of_work',
                    'message': 'Place of work not specified'
                })
            
            # Years of experience is optional for lawyers/paralegals - only add if provided
            if user.years_of_experience:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'years_of_experience',
                    'label': 'Years of Experience (Optional)',
                    'value': str(user.years_of_experience),
                    'status': 'verified'
                })
        
        elif role_name == 'law_firm':
            if user.firm_name:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'firm_name',
                    'label': 'Firm Name',
                    'value': user.firm_name,
                    'status': 'verified'
                })
            else:
                by_step['role_specific']['issues'].append({
                    'type': 'missing_field',
                    'field': 'firm_name',
                    'message': 'Firm name is missing'
                })
            
            if user.managing_partner:
                by_step['role_specific']['verified_fields'].append({
                    'field': 'managing_partner',
                    'label': 'Managing Partner',
                    'value': user.managing_partner,
                    'status': 'verified'
                })
            else:
                by_step['role_specific']['issues'].append({
                    'type': 'missing_field',
                    'field': 'managing_partner',
                    'message': 'Managing partner not specified'
                })
        
        if not by_step['role_specific']['issues']:
            by_step['role_specific']['status'] = 'complete'
        
        # STEP 5: FINAL
        # Final step is complete when all other steps are complete and status is verified
        all_steps_complete = all(
            by_step[step]['status'] == 'complete' 
            for step in ['documents', 'identity', 'contact', 'role_specific']
        )
        
        if all_steps_complete and obj.status == 'verified':
            by_step['final']['status'] = 'complete'
        elif all_steps_complete:
            by_step['final']['status'] = 'ready_for_approval'
            by_step['final']['issues'].append({
                'type': 'action_required',
                'message': 'All requirements met - ready for final admin approval'
            })
        
        # Calculate overall status
        has_missing_items = any(
            len(by_step[step]['issues']) > 0 
            for step in ['documents', 'identity', 'contact', 'role_specific']
        )
        
        is_ready_for_approval = (
            all_steps_complete and 
            obj.status == 'pending'
        )
        
        # Generate summary
        total_issues = sum(len(by_step[step]['issues']) for step in by_step.keys())
        
        if is_ready_for_approval:
            summary = "✅ All requirements met - ready for final approval"
        elif obj.status == 'verified':
            summary = "✅ Verification complete"
        else:
            step_summaries = []
            for step in ['documents', 'identity', 'contact', 'role_specific']:
                issue_count = len(by_step[step]['issues'])
                if issue_count > 0:
                    step_label = dict(obj.VERIFICATION_STEP).get(step, step)
                    step_summaries.append(f"{step_label}: {issue_count} issue(s)")
            
            if step_summaries:
                summary = f"⚠️ {total_issues} issue(s) found - " + ", ".join(step_summaries)
            else:
                summary = "✅ All information provided - awaiting verification"
        
        return {
            'has_missing_items': has_missing_items,
            'is_ready_for_approval': is_ready_for_approval,
            'by_step': by_step,
            'current_step': obj.current_step,
            'summary': summary
        }

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
            # Auto-verified roles - no documents required
            'law_student': [],
            'citizen': [],
            'lecturer': []
        }
        
        required = requirements.get(role_name, [])
        
        # Add upload status for each required document
        user_docs = Document.objects.filter(user=obj.user, is_active=True)
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
