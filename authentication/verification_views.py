"""
Verification Views and APIs
Handles document upload, verification workflows, and admin approval
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import PolaUser, Verification, Document, VerificationDocument
from .verification_serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    VerificationSerializer,
    VerificationActionSerializer,
    UserVerificationStatusSerializer
)


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class DocumentUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for uploading documents with form data
    Handles file uploads with multipart/form-data
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        """Users can only see their own documents, admins see all"""
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Document.objects.none()
        
        if self.request.user.is_staff:
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Upload a verification document",
        manual_parameters=[
            openapi.Parameter('document_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document type'),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document title'),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document description'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Document file (PDF, JPG, PNG, DOC)'),
        ],
        responses={201: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def create(self, request, *args, **kwargs):
        """Upload a new document"""
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return full document details
        output_serializer = DocumentSerializer(serializer.instance, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update a document",
        manual_parameters=[
            openapi.Parameter('document_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document type'),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document title'),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document description'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Document file (PDF, JPG, PNG, DOC)'),
        ],
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def update(self, request, *args, **kwargs):
        """Update a document (full update)"""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a document",
        manual_parameters=[
            openapi.Parameter('document_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document type'),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document title'),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document description'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='Document file (PDF, JPG, PNG, DOC)'),
        ],
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a document"""
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Automatically set the user when uploading a document"""
        document = serializer.save(user=self.request.user)
        return document


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for viewing documents
    For file uploads, use DocumentUploadViewSet
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own documents, admins see all"""
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Document.objects.none()
        
        if self.request.user.is_staff:
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Upload a verification document",
        manual_parameters=[
            openapi.Parameter('document_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document type'),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document title'),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document description'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Document file (PDF, JPG, PNG, DOC)'),
        ],
        responses={201: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def create(self, request, *args, **kwargs):
        """Upload a new document"""
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return full document details
        output_serializer = DocumentSerializer(serializer.instance, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="List all documents",
        responses={200: DocumentSerializer(many=True)},
        tags=['Verification - Documents']
    )
    def list(self, request, *args, **kwargs):
        """List user's documents"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get document details",
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def retrieve(self, request, *args, **kwargs):
        """Get a specific document"""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a document",
        manual_parameters=[
            openapi.Parameter('document_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document type'),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='Document title'),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document description'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='Document file (PDF, JPG, PNG, DOC)'),
        ],
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def update(self, request, *args, **kwargs):
        """Update a document (full update)"""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a document",
        manual_parameters=[
            openapi.Parameter('document_type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document type'),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document title'),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description='Document description'),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description='Document file (PDF, JPG, PNG, DOC)'),
        ],
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a document"""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a document",
        responses={204: 'No Content'},
        tags=['Verification - Documents']
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a document"""
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Automatically set the user when uploading a document"""
        document = serializer.save(user=self.request.user)
        return document

    # Temporarily commented out custom actions to debug Swagger issue
    # @swagger_auto_schema(
    #     method='post',
    #     request_body=VerificationActionSerializer,
    #     responses={200: DocumentSerializer},
    #     tags=['Verification - Admin']
    # )
    # @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    # def verify(self, request, pk=None):
    #     """
    #     Admin endpoint to verify a document
    #     POST /documents/{id}/verify/
    #     Body: {"status": "verified", "notes": "Document approved"}
    #     """
    #     document = self.get_object()
    #     serializer = VerificationActionSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     
    #     document.verify(
    #         verified_by=request.user,
    #         status=serializer.validated_data.get('status', 'verified'),
    #         notes=serializer.validated_data.get('notes')
    #     )
    #     return Response({
    #         'message': 'Document verification status updated',
    #         'document': DocumentSerializer(document, context={'request': request}).data
    #     })

    # @swagger_auto_schema(
    #     method='post',
    #     request_body=openapi.Schema(
    #         type=openapi.TYPE_OBJECT,
    #         properties={'reason': openapi.Schema(type=openapi.TYPE_STRING)}
    #     ),
    #     responses={200: DocumentSerializer},
    #     tags=['Verification - Admin']
    # )
    # @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    # def reject(self, request, pk=None):
    #     """
    #     Admin endpoint to reject a document
    #     POST /documents/{id}/reject/
    #     Body: {"reason": "Document is not clear"}
    #     """
    #     document = self.get_object()
    #     reason = request.data.get('reason', '')
    #     
    #     if not reason:
    #         return Response({
    #             'error': 'Rejection reason is required'
    #         }, status=status.HTTP_400_BAD_REQUEST)
    #     
    #     document.verify(
    #         verified_by=request.user,
    #         status='rejected',
    #         notes=reason
    #     )
    #     
    #     return Response({
    #         'message': 'Document rejected',
    #         'document': DocumentSerializer(document, context={'request': request}).data
    #     })


class VerificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing verification status
    Users can view their own verification status
    Admins can view all verifications
    """
    serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Users see their own verification, admins see all"""
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Verification.objects.none()
        
        if self.request.user.is_staff:
            return Verification.objects.all()
        return Verification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all verifications",
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - User']
    )
    def list(self, request, *args, **kwargs):
        """List verifications"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get verification details",
        responses={200: VerificationSerializer},
        tags=['Verification - User']
    )
    def retrieve(self, request, *args, **kwargs):
        """Get a specific verification"""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        method='get',
        responses={200: VerificationSerializer},
        tags=['Verification - User']
    )
    @action(detail=False, methods=['get'])
    def my_status(self, request):
        """
        Get current user's verification status
        GET /verifications/my_status/
        """
        try:
            verification = Verification.objects.get(user=request.user)
            serializer = VerificationSerializer(verification, context={'request': request})
            return Response(serializer.data)
        except Verification.DoesNotExist:
            return Response({
                'error': 'Verification record not found',
                'message': 'Please contact support to create a verification record'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        method='get',
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - Admin']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """
        Get all pending verifications (Admin only)
        GET /verifications/pending/
        """
        pending_verifications = Verification.objects.filter(status='pending')
        serializer = VerificationSerializer(pending_verifications, many=True, context={'request': request})
        return Response({
            'count': pending_verifications.count(),
            'results': serializer.data
        })

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, description="User role", type=openapi.TYPE_STRING)
        ],
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - Admin']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def by_role(self, request):
        """
        Get verifications grouped by user role (Admin only)
        GET /verifications/by_role/?role=advocate
        """
        role = request.query_params.get('role')
        if not role:
            return Response({
                'error': 'Please provide a role parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        verifications = Verification.objects.filter(
            user__user_role__role_name=role
        )
        serializer = VerificationSerializer(verifications, many=True, context={'request': request})
        return Response({
            'role': role,
            'count': verifications.count(),
            'results': serializer.data
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'notes': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        responses={200: VerificationSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Admin endpoint to approve a user's verification
        POST /verifications/{id}/approve/
        Body: {"notes": "All documents verified"}
        """
        verification = self.get_object()
        notes = request.data.get('notes', '')

        # Check if already verified
        if verification.status == 'verified':
            return Response({
                'error': 'User is already verified'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has required documents based on role
        user = verification.user
        role_name = user.user_role.role_name if user.user_role else None

        # Get required documents for this role
        required_docs = self._get_required_documents(role_name)
        
        # Check if all required documents are uploaded and verified
        user_docs = Document.objects.filter(user=user, verification_status='verified')
        uploaded_doc_types = set(user_docs.values_list('document_type', flat=True))
        
        missing_docs = [doc for doc in required_docs if doc not in uploaded_doc_types]
        
        if missing_docs:
            return Response({
                'error': 'Missing required documents',
                'missing_documents': missing_docs,
                'message': 'All required documents must be verified before approving user verification'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Approve verification
        verification.status = 'verified'
        verification.verified_by = request.user
        verification.verification_date = timezone.now()
        verification.verification_notes = notes
        verification.save()

        # Update user's is_verified status
        user.is_verified = True
        user.save()

        return Response({
            'message': 'User verification approved',
            'verification': VerificationSerializer(verification, context={'request': request}).data
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'reason': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        responses={200: VerificationSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """
        Admin endpoint to reject a user's verification
        POST /verifications/{id}/reject/
        Body: {"reason": "Invalid documents"}
        """
        verification = self.get_object()
        reason = request.data.get('reason', '')

        if not reason:
            return Response({
                'error': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        verification.reject(verified_by=request.user, reason=reason)

        # Update user's is_verified status
        verification.user.is_verified = False
        verification.user.save()

        return Response({
            'message': 'User verification rejected',
            'verification': VerificationSerializer(verification, context={'request': request}).data
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'documents': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: VerificationSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def request_documents(self, request, pk=None):
        """
        Admin endpoint to request additional documents
        POST /verifications/{id}/request_documents/
        Body: {"documents": ["practice_license", "work_certificate"], "message": "Please upload..."}
        """
        verification = self.get_object()
        documents = request.data.get('documents', [])
        message = request.data.get('message', 'Additional documents required')

        if not documents or not isinstance(documents, list):
            return Response({
                'error': 'Please provide a list of document types'
            }, status=status.HTTP_400_BAD_REQUEST)

        verification.verification_notes = f"{verification.verification_notes or ''}\n\nRequested documents: {', '.join(documents)}\nMessage: {message}"
        verification.save()

        return Response({
            'message': 'Document request sent to user',
            'verification': VerificationSerializer(verification, context={'request': request}).data
        })

    def _get_required_documents(self, role_name):
        """Get required document types for each role"""
        requirements = {
            'advocate': ['roll_number_cert', 'practice_license', 'work_certificate'],
            'lawyer': ['professional_cert', 'employment_letter'],
            'paralegal': ['professional_cert', 'employment_letter'],
            'law_firm': ['business_license', 'registration_cert'],
            'law_student': [],  # Auto-verified
            'citizen': []  # Auto-verified
        }
        return requirements.get(role_name, [])


class AdminVerificationDashboardViewSet(viewsets.ViewSet):
    """
    Admin dashboard for verification management
    Provides statistics and bulk operations
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        method='get',
        tags=['Verification - Admin Dashboard']
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get verification statistics
        GET /admin-verification/statistics/
        """
        total_users = PolaUser.objects.count()
        verified_users = PolaUser.objects.filter(is_verified=True).count()
        pending_verifications = Verification.objects.filter(status='pending').count()
        rejected_verifications = Verification.objects.filter(status='rejected').count()
        
        # By role
        role_stats = {}
        from .models import UserRole
        for role in UserRole.objects.all():
            role_stats[role.role_name] = {
                'total': PolaUser.objects.filter(user_role=role).count(),
                'verified': PolaUser.objects.filter(user_role=role, is_verified=True).count(),
                'pending': Verification.objects.filter(user__user_role=role, status='pending').count()
            }

        return Response({
            'overview': {
                'total_users': total_users,
                'verified_users': verified_users,
                'pending_verifications': pending_verifications,
                'rejected_verifications': rejected_verifications,
                'verification_rate': round((verified_users / total_users * 100) if total_users > 0 else 0, 2)
            },
            'by_role': role_stats
        })

    @swagger_auto_schema(
        method='get',
        responses={200: DocumentSerializer(many=True)},
        tags=['Verification - Admin Dashboard']
    )
    @action(detail=False, methods=['get'])
    def pending_documents(self, request):
        """
        Get all pending documents for review
        GET /admin-verification/pending_documents/
        """
        pending_docs = Document.objects.filter(verification_status='pending')
        serializer = DocumentSerializer(pending_docs, many=True, context={'request': request})
        
        return Response({
            'count': pending_docs.count(),
            'documents': serializer.data
        })

    @swagger_auto_schema(
        method='get',
        tags=['Verification - Admin Dashboard']
    )
    @action(detail=False, methods=['get'])
    def users_needing_review(self, request):
        """
        Get users who have uploaded all required documents and need review
        GET /admin-verification/users_needing_review/
        """
        # Get users with pending verification who have uploaded documents
        users_with_docs = PolaUser.objects.filter(
            verification__status='pending',
            documents__isnull=False
        ).distinct()

        results = []
        for user in users_with_docs:
            role_name = user.user_role.role_name if user.user_role else None
            required_docs = self._get_required_documents(role_name)
            
            user_docs = Document.objects.filter(user=user)
            uploaded_doc_types = set(user_docs.values_list('document_type', flat=True))
            
            # Check if all required documents are uploaded
            has_all_docs = all(doc in uploaded_doc_types for doc in required_docs)
            
            if has_all_docs:
                results.append({
                    'user_id': user.id,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'role': role_name,
                    'documents_count': user_docs.count(),
                    'verified_documents': user_docs.filter(verification_status='verified').count(),
                    'pending_documents': user_docs.filter(verification_status='pending').count()
                })

        return Response({
            'count': len(results),
            'users': results
        })

    def _get_required_documents(self, role_name):
        """Get required document types for each role"""
        requirements = {
            'advocate': ['roll_number_cert', 'practice_license', 'work_certificate'],
            'lawyer': ['professional_cert', 'employment_letter'],
            'paralegal': ['professional_cert', 'employment_letter'],
            'law_firm': ['business_license', 'registration_cert'],
            'law_student': [],
            'citizen': []
        }
        return requirements.get(role_name, [])
