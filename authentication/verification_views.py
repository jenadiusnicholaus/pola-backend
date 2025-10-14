"""
Verification Views and APIs
Handles document upload, verification workflows, and admin approval
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, DateFilter, BooleanFilter
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
from utils.pagination import StandardResultsSetPagination


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class VerificationFilter(FilterSet):
    """
    Custom filter for Verification queryset
    Supports filtering by status, role, dates, and step-based fields
    """
    # Basic filters
    status = CharFilter(field_name='status', lookup_expr='iexact')
    role = CharFilter(field_name='user__user_role__role_name', lookup_expr='iexact')
    
    # Date filters
    created_after = DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateFilter(field_name='created_at', lookup_expr='lte')
    verified_after = DateFilter(field_name='verification_date', lookup_expr='gte')
    verified_before = DateFilter(field_name='verification_date', lookup_expr='lte')
    
    # Step filters
    current_step = CharFilter(field_name='current_step', lookup_expr='iexact')
    
    class Meta:
        model = Verification
        fields = ['status', 'role', 'current_step']


class DocumentUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for uploading documents with base64 support
    Handles file uploads with JSON data containing base64 encoded files
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
        operation_description="Upload a verification document using base64 encoding",
        request_body=DocumentUploadSerializer,
        responses={201: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def create(self, request, *args, **kwargs):
        """Upload a new document using base64 encoding"""
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
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
        operation_description="Update a document using base64 encoding",
        request_body=DocumentUploadSerializer,
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def update(self, request, *args, **kwargs):
        """Update a document (full update) using base64 encoding"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = DocumentUploadSerializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Partially update a document using base64 encoding",
        request_body=DocumentUploadSerializer,
        responses={200: DocumentSerializer},
        tags=['Verification - Documents']
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a document using base64 encoding"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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

    @swagger_auto_schema(
        method='post',
        request_body=VerificationActionSerializer,
        responses={200: DocumentSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify(self, request, pk=None):
        """
        Admin endpoint to verify a document
        POST /documents/{id}/verify/
        Body: {"status": "verified", "notes": "Document approved"}
        """
        document = self.get_object()
        serializer = VerificationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        document.verify(
            verified_by=request.user,
            status=serializer.validated_data.get('status', 'verified'),
            notes=serializer.validated_data.get('notes')
        )
        return Response({
            'message': 'Document verification status updated',
            'document': DocumentSerializer(document, context={'request': request}).data
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'reason': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        responses={200: DocumentSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """
        Admin endpoint to reject a document
        POST /documents/{id}/reject/
        Body: {"reason": "Document is not clear"}
        """
        document = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({
                'error': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        document.verify(
            verified_by=request.user,
            status='rejected',
            notes=reason
        )
        
        return Response({
            'message': 'Document rejected',
            'document': DocumentSerializer(document, context={'request': request}).data
        })


class VerificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing verification status
    Users can view their own verification status
    Admins can view all verifications with comprehensive filtering support
    
    Filtering options:
    - status: Filter by verification status (pending, verified, rejected)
    - role: Filter by user role (advocate, lawyer, paralegal, law_firm)
    - current_step: Filter by current verification step (documents, identity, contact, role_specific, final)
    - created_after/created_before: Filter by creation date
    - verified_after/verified_before: Filter by verification date
    - search: Search by user email, name, or verification notes
    
    Example queries:
    - /verifications/?status=pending&role=advocate
    - /verifications/?current_step=identity&created_after=2025-01-01
    - /verifications/?search=john@example.com
    """
    serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VerificationFilter
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'verification_notes']
    ordering_fields = ['created_at', 'verification_date', 'status', 'current_step']
    ordering = ['-created_at']  # Default ordering
    pagination_class = StandardResultsSetPagination  # Use custom pagination

    def get_queryset(self):
        """Users see their own verification, admins see verification-required roles only"""
        # Handle schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Verification.objects.none()
        
        if self.request.user.is_staff:
            # Exclude auto-verified roles and admin users from verification lists
            auto_verify_roles = ['citizen', 'law_student', 'lecturer']
            return Verification.objects.exclude(
                user__user_role__role_name__in=auto_verify_roles
            ).exclude(
                user__is_staff=True  # Exclude admin/staff users
            )
        return Verification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="""List all verifications with filtering support.
        
        Query Parameters:
        - status: Filter by status (pending, verified, rejected)
        - role: Filter by user role (advocate, lawyer, paralegal, law_firm)
        - current_step: Filter by verification step (documents, identity, contact, role_specific, final)
        - created_after: Filter verifications created after this date (YYYY-MM-DD)
        - created_before: Filter verifications created before this date (YYYY-MM-DD)
        - verified_after: Filter verifications verified after this date (YYYY-MM-DD)
        - verified_before: Filter verifications verified before this date (YYYY-MM-DD)
        - search: Search by email, name, or notes
        - ordering: Order by field (created_at, verification_date, status, current_step). Prefix with - for descending.
        
        Examples:
        - /verifications/?status=pending&role=advocate
        - /verifications/?current_step=identity&created_after=2025-01-01
        - /verifications/?search=john@example.com&ordering=-created_at
        """,
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by user role", type=openapi.TYPE_STRING),
            openapi.Parameter('current_step', openapi.IN_QUERY, description="Filter by current step", type=openapi.TYPE_STRING),
            openapi.Parameter('created_after', openapi.IN_QUERY, description="Created after date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_before', openapi.IN_QUERY, description="Created before date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('verified_after', openapi.IN_QUERY, description="Verified after date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('verified_before', openapi.IN_QUERY, description="Verified before date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by email, name, or notes", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field (prefix with - for descending)", type=openapi.TYPE_STRING),
        ],
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - User']
    )
    def list(self, request, *args, **kwargs):
        """List verifications with filtering, search, and ordering"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        method='get',
        operation_description="""Get all verifications with pagination (Admin only) with filtering support.
        
        Query Parameters (same as list endpoint):
        - status: Filter by status (pending, verified, rejected)
        - role: Filter by user role (advocate, lawyer, paralegal, law_firm)
        - current_step: Filter by verification step
        - created_after/created_before: Date range filters
        - search: Search by email, name, or notes
        - ordering: Order results
        - page: Page number
        - page_size: Results per page
        
        Examples:
        - /verifications/all/?status=pending&role=advocate
        - /verifications/all/?search=john&current_step=identity
        """,
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by user role", type=openapi.TYPE_STRING),
            openapi.Parameter('current_step', openapi.IN_QUERY, description="Filter by current step", type=openapi.TYPE_STRING),
            openapi.Parameter('created_after', openapi.IN_QUERY, description="Created after date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_before', openapi.IN_QUERY, description="Created before date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by email, name, or notes", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - Admin']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def all(self, request):
        """
        Get all verifications with pagination (Admin only) with filtering - excludes auto-verified roles and admin users
        GET /verifications/all/
        """
        # Get the base queryset (already filtered by get_queryset)
        queryset = self.filter_queryset(self.get_queryset())
        
        # Use DRF pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VerificationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = VerificationSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

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
        responses={200: VerificationSerializer(many=True)},
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
        operation_description="""Get all pending verifications (Admin only) with filtering support and pagination.
        
        Query Parameters:
        - role: Filter by user role
        - current_step: Filter by verification step
        - created_after/created_before: Date range filters
        - search: Search by email, name, or notes
        - ordering: Order results
        - page: Page number
        - page_size: Results per page
        
        Examples:
        - /verifications/pending/?role=advocate
        - /verifications/pending/?current_step=documents&created_after=2025-01-01
        """,
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, description="Filter by user role", type=openapi.TYPE_STRING),
            openapi.Parameter('current_step', openapi.IN_QUERY, description="Filter by current step", type=openapi.TYPE_STRING),
            openapi.Parameter('created_after', openapi.IN_QUERY, description="Created after date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_before', openapi.IN_QUERY, description="Created before date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by email, name, or notes", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - Admin']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending(self, request):
        """
        Get all pending verifications (Admin only) with filtering and pagination - excludes auto-verified roles and admin users
        GET /verifications/pending/
        """
        # Start with pending verifications
        auto_verify_roles = ['citizen', 'law_student', 'lecturer']
        queryset = Verification.objects.filter(
            status='pending'
        ).exclude(
            user__user_role__role_name__in=auto_verify_roles
        ).exclude(
            user__is_staff=True  # Exclude admin/staff users
        )
        
        # Apply filters manually since this is a custom action
        # Apply role filter
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(user__user_role__role_name__iexact=role)
        
        # Apply step filter
        current_step = request.query_params.get('current_step')
        if current_step:
            queryset = queryset.filter(current_step__iexact=current_step)
        
        # Apply date filters
        created_after = request.query_params.get('created_after')
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
            
        created_before = request.query_params.get('created_before')
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        # Apply search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(verification_notes__icontains=search)
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Use DRF pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VerificationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = VerificationSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        method='get',
        operation_description="""Get verifications by user role (Admin only) with additional filtering and pagination.
        
        Required Parameter:
        - role: User role to filter by (advocate, lawyer, paralegal, law_firm)
        
        Optional Parameters:
        - status: Filter by verification status
        - current_step: Filter by current step
        - created_after/created_before: Date range filters
        - search: Search by email, name, or notes
        - ordering: Order results
        - page: Page number
        - page_size: Results per page
        
        Examples:
        - /verifications/by_role/?role=advocate&status=pending
        - /verifications/by_role/?role=lawyer&current_step=identity
        """,
        manual_parameters=[
            openapi.Parameter('role', openapi.IN_QUERY, description="User role (required)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('current_step', openapi.IN_QUERY, description="Filter by current step", type=openapi.TYPE_STRING),
            openapi.Parameter('created_after', openapi.IN_QUERY, description="Created after date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_before', openapi.IN_QUERY, description="Created before date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by email, name, or notes", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={200: VerificationSerializer(many=True)},
        tags=['Verification - Admin']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def by_role(self, request):
        """
        Get verifications by user role (Admin only) with additional filtering and pagination
        GET /verifications/by_role/?role=advocate&status=pending
        """
        role = request.query_params.get('role')
        if not role:
            return Response({
                'error': 'Please provide a role parameter'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start with role filter
        queryset = Verification.objects.filter(
            user__user_role__role_name__iexact=role
        )
        
        # Apply additional filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)
        
        current_step = request.query_params.get('current_step')
        if current_step:
            queryset = queryset.filter(current_step__iexact=current_step)
        
        created_after = request.query_params.get('created_after')
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
            
        created_before = request.query_params.get('created_before')
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(verification_notes__icontains=search)
            )
        
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Use DRF pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VerificationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = VerificationSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

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

        # Check if this role is auto-verified (no document verification needed)
        auto_verify_roles = ['citizen', 'law_student', 'lecturer']
        if role_name in auto_verify_roles:
            return Response({
                'error': 'This user role is auto-verified and does not require admin approval',
                'message': f'{role_name.replace("_", " ").title()} users are automatically verified upon registration'
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # Note: is_verified is a property that automatically reflects verification status
        # No need to set it directly

        return Response({
            'message': 'User verification approved',
            'verification': VerificationSerializer(verification, context={'request': request}).data
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'step': openapi.Schema(type=openapi.TYPE_STRING),
                'notes': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: VerificationSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verify_step(self, request, pk=None):
        """
        Admin endpoint to verify a specific step of the verification process
        POST /verifications/{id}/verify_step/
        Body: {"step": "identity", "notes": "Identity verified"}
        """
        verification = self.get_object()
        step = request.data.get('step')
        notes = request.data.get('notes', '')
        
        if not step:
            return Response({
                'error': 'Step is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the step
        success = verification.verify_step(step, request.user, notes)
        
        if success:
            return Response({
                'message': f'{step} step verified successfully',
                'verification': VerificationSerializer(verification, context={'request': request}).data
            })
        else:
            return Response({
                'error': f'Cannot verify {step} step. Current step is {verification.current_step}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'step': openapi.Schema(type=openapi.TYPE_STRING),
                'reason': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: VerificationSerializer},
        tags=['Verification - Admin']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject_step(self, request, pk=None):
        """
        Admin endpoint to reject a specific step of the verification process
        POST /verifications/{id}/reject_step/
        Body: {"step": "documents", "reason": "Documents are unclear"}
        """
        verification = self.get_object()
        step = request.data.get('step')
        reason = request.data.get('reason', '')
        
        if not step:
            return Response({
                'error': 'Step is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not reason:
            return Response({
                'error': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if this is the current step or if we can reject it
        valid_steps = [choice[0] for choice in verification.VERIFICATION_STEP]
        if step not in valid_steps:
            return Response({
                'error': f'Invalid step. Valid steps are: {", ".join(valid_steps)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reject the verification with step-specific reason
        step_display = dict(verification.VERIFICATION_STEP).get(step, step)
        full_reason = f'{step_display} rejected: {reason}'
        
        verification.reject(verified_by=request.user, reason=full_reason)
        
        return Response({
            'message': f'{step} step rejected',
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
        # Auto-verified roles have no document requirements
        auto_verify_roles = ['citizen', 'law_student', 'lecturer']
        if role_name in auto_verify_roles:
            return []
            
        requirements = {
            'advocate': ['roll_number_cert', 'practice_license', 'work_certificate'],
            'lawyer': ['professional_cert', 'employment_letter'],
            'paralegal': ['professional_cert', 'employment_letter'],
            'law_firm': ['business_license', 'registration_cert'],
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
        Get verification statistics - separates auto-verified from manual verification roles, excludes admin users
        GET /admin-verification/statistics/
        """
        auto_verify_roles = ['citizen', 'law_student', 'lecturer']
        
        # Total users (excluding admin/staff users)
        total_users = PolaUser.objects.exclude(is_staff=True).count()
        auto_verified_users = PolaUser.objects.filter(
            user_role__role_name__in=auto_verify_roles
        ).exclude(is_staff=True).count()
        manual_verification_users = total_users - auto_verified_users
        
        # Manual verification statistics (excluding auto-verified roles and admin users)
        manual_verified = PolaUser.objects.filter(
            verification__status='verified'
        ).exclude(
            user_role__role_name__in=auto_verify_roles
        ).exclude(
            is_staff=True
        ).count()
        
        manual_pending = Verification.objects.filter(
            status='pending'
        ).exclude(
            user__user_role__role_name__in=auto_verify_roles
        ).exclude(
            user__is_staff=True
        ).count()
        
        manual_rejected = Verification.objects.filter(
            status='rejected'
        ).exclude(
            user__user_role__role_name__in=auto_verify_roles
        ).exclude(
            user__is_staff=True
        ).count()
        
        # By role stats (excluding admin users)
        role_stats = {}
        from .models import UserRole
        for role in UserRole.objects.all():
            is_auto_verify = role.role_name in auto_verify_roles
            role_stats[role.role_name] = {
                'total': PolaUser.objects.filter(user_role=role).exclude(is_staff=True).count(),
                'verified': PolaUser.objects.filter(
                    user_role=role, 
                    verification__status='verified'
                ).exclude(is_staff=True).count(),
                'pending': Verification.objects.filter(
                    user__user_role=role, 
                    status='pending'
                ).exclude(user__is_staff=True).count(),
                'is_auto_verified': is_auto_verify,
                'verification_type': 'auto' if is_auto_verify else 'manual'
            }

        return Response({
            'overview': {
                'total_users': total_users,
                'auto_verified_users': auto_verified_users,
                'manual_verification_users': manual_verification_users,
                'manual_verified': manual_verified,
                'manual_pending': manual_pending,
                'manual_rejected': manual_rejected,
                'manual_verification_rate': round((manual_verified / manual_verification_users * 100) if manual_verification_users > 0 else 0, 2)
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
    def debug_documents(self, request):
        """
        Debug endpoint to check document status
        GET /admin-verification/debug_documents/
        """
        all_docs = Document.objects.all()
        active_docs = Document.objects.filter(is_active=True)
        
        debug_info = {
            'total_documents': all_docs.count(),
            'active_documents': active_docs.count(),
            'inactive_documents': all_docs.filter(is_active=False).count(),
            'documents_by_status': {
                'pending': active_docs.filter(verification_status='pending').count(),
                'verified': active_docs.filter(verification_status='verified').count(),
                'rejected': active_docs.filter(verification_status='rejected').count(),
            },
            'documents_by_user': []
        }
        
        # Get document count per user
        for user in PolaUser.objects.all():
            user_docs = Document.objects.filter(user=user, is_active=True)
            if user_docs.exists():
                debug_info['documents_by_user'].append({
                    'user_id': user.id,
                    'user_email': user.email,
                    'user_name': f"{user.first_name} {user.last_name}",
                    'total_docs': user_docs.count(),
                    'verified_docs': user_docs.filter(verification_status='verified').count(),
                    'pending_docs': user_docs.filter(verification_status='pending').count(),
                    'rejected_docs': user_docs.filter(verification_status='rejected').count(),
                })
        
        return Response(debug_info)

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
        # Auto-verified roles have no document requirements
        auto_verify_roles = ['citizen', 'law_student', 'lecturer']
        if role_name in auto_verify_roles:
            return []
            
        requirements = {
            'advocate': ['roll_number_cert', 'practice_license', 'work_certificate'],
            'lawyer': ['professional_cert', 'employment_letter'],
            'paralegal': ['professional_cert', 'employment_letter'],
            'law_firm': ['business_license', 'registration_cert'],
        }
        return requirements.get(role_name, [])
