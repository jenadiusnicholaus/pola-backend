"""
Document Template Views
Handles template listing, field retrieval, validation, and document generation
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.core.files.base import ContentFile
from django.utils import timezone
import os
import uuid
import tempfile

from .models import (
    DocumentTemplate,
    TemplateField,
    UserDocument,
    UserDocumentData
)
from .serializers import (
    DocumentTemplateListSerializer,
    DocumentTemplateDetailSerializer,
    UserDocumentSerializer,
    GenerateDocumentSerializer,
    ValidateDocumentDataSerializer
)
from .utils.pdf_generator import PDFGenerator, validate_field_data


class DocumentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing and retrieving document templates
    
    Endpoints:
    - GET /api/v1/templates/ - List all templates
    - GET /api/v1/templates/{id}/ - Get template with fields
    - POST /api/v1/templates/{id}/validate/ - Validate data
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_free']
    search_fields = ['name', 'name_sw', 'description', 'description_sw']
    ordering_fields = ['order', 'usage_count', 'created_at']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        """Only return active templates"""
        return DocumentTemplate.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        """Use different serializers for list and detail"""
        if self.action == 'list':
            return DocumentTemplateListSerializer
        return DocumentTemplateDetailSerializer
    
    def get_serializer_context(self):
        """Add language to serializer context"""
        context = super().get_serializer_context()
        # Get language from query param, default to English
        context['language'] = self.request.query_params.get('language', 'en')
        return context
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        Validate user's filled data before generation
        
        POST /api/v1/templates/{id}/validate/
        Body: {
            "language": "en",
            "data": {"field_name": "value", ...}
        }
        """
        template = self.get_object()
        serializer = ValidateDocumentDataSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        language = serializer.validated_data['language']
        data = serializer.validated_data['data']
        
        # Validate each field
        errors = {}
        warnings = []
        
        # Get all template fields
        fields = template.fields.all()
        
        for field in fields:
            field_name = field.field_name
            value = data.get(field_name, '')
            
            # Validate field
            is_valid, error_msg = validate_field_data(field, value)
            
            if not is_valid:
                errors[field_name] = error_msg
        
        # Check for extra fields not in template
        template_field_names = {f.field_name for f in fields}
        extra_fields = set(data.keys()) - template_field_names
        if extra_fields:
            warnings.append(f"Extra fields will be ignored: {', '.join(extra_fields)}")
        
        if errors:
            return Response({
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'valid': True,
            'message': 'All fields are valid',
            'warnings': warnings
        })


class UserDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user's generated documents
    
    Endpoints:
    - GET /api/v1/documents/ - List user's documents
    - GET /api/v1/documents/{id}/ - Get document details
    - POST /api/v1/documents/generate/ - Generate new document
    - GET /api/v1/documents/{id}/download/ - Download PDF
    - DELETE /api/v1/documents/{id}/ - Delete document
    """
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated for testing
    serializer_class = UserDocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template', 'language', 'status']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only return user's own documents"""
        return UserDocument.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new document from template
        
        POST /api/v1/documents/generate/
        Body: {
            "template_id": 1,
            "language": "en",
            "document_title": "My Employment Contract",
            "data": {
                "employee_name": "John Doe",
                "employer_name": "ABC Company",
                ...
            }
        }
        """
        serializer = GenerateDocumentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        template_id = serializer.validated_data['template_id']
        language = serializer.validated_data['language']
        document_title = serializer.validated_data.get('document_title', '')
        user_data = serializer.validated_data['data']
        
        # Get template
        template = DocumentTemplate.objects.get(id=template_id)
        
        # Check if user needs to pay for premium template
        if not template.is_free and template.price > 0:
            # TODO: Implement payment check
            # For now, allow free generation
            pass
        
        # Create user document record
        user_document = UserDocument.objects.create(
            user=request.user if request.user.is_authenticated else None,
            template=template,
            language=language,
            document_title=document_title or template.name,
            is_paid=template.is_free or template.price == 0,
            payment_amount=template.price if not template.is_free else 0
        )
        
        # Save field data
        for field in template.fields.all():
            if field.field_name in user_data:
                UserDocumentData.objects.create(
                    user_document=user_document,
                    field=field,
                    value=str(user_data[field.field_name])
                )
        
        # Mark as generating
        user_document.mark_as_generating()
        
        try:
            # Get template content/filename in requested language
            template_content_or_file = (
                template.template_content_sw if language == 'sw'
                else template.template_content_en
            )
            
            # Check if it's a filename or full HTML content
            # If it starts with <!DOCTYPE or <html>, it's full HTML content
            # Otherwise, treat it as a filename and load from file
            if template_content_or_file.strip().startswith(('<!DOCTYPE', '<html', '<HTML')):
                # It's full HTML content stored in database
                template_content = template_content_or_file
            else:
                # It's a filename, load from templates directory
                from django.conf import settings
                template_path = os.path.join(
                    settings.BASE_DIR,
                    'document_templates',
                    'templates',
                    template_content_or_file
                )
                
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            
            # Generate PDF
            pdf_generator = PDFGenerator()
            
            # Create filename (FileField's upload_to will handle the directory structure)
            filename = f"{template.name.replace(' ', '_')}_{user_document.id}_{uuid.uuid4().hex[:8]}.pdf"
            
            # Generate document to a temporary location first
            from django.conf import settings
            import tempfile
            
            # Create temp file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(temp_fd)
            
            # Generate document
            pdf_path = pdf_generator.generate_document(
                template_content,
                user_data,
                temp_path
            )
            
            # Save file to model (FileField will handle upload_to path automatically)
            with open(pdf_path, 'rb') as f:
                user_document.generated_file.save(
                    filename,
                    ContentFile(f.read()),
                    save=True  # Save immediately to persist the file path
                )
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            # Mark as completed (file path already saved above)
            user_document.mark_as_completed()
            
            # Increment template usage
            template.increment_usage()
            
            # Return success response
            serializer = UserDocumentSerializer(user_document, context={'request': request})
            return Response({
                'success': True,
                'message': 'Document generated successfully',
                'document': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Mark as failed
            user_document.mark_as_failed(str(e))
            
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Document generation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download generated document
        
        GET /api/v1/documents/{id}/download/
        """
        user_document = self.get_object()
        
        if not user_document.generated_file:
            return Response({
                'error': 'Document file not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Increment download counter
        user_document.increment_download()
        
        # Return file URL
        return Response({
            'download_url': request.build_absolute_uri(user_document.generated_file.url),
            'filename': os.path.basename(user_document.generated_file.name),
            'file_size': user_document.generated_file.size
        })
