"""
Admin Consultant Management Views

This module provides admin APIs for reviewing and managing consultant registration requests.
Admins can approve/reject applications and manage consultant profiles.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone

from .models import (
    ConsultantRegistrationRequest,
    ConsultantProfile,
)
from .public_serializers import (
    ConsultantRegistrationRequestSerializer,
    ConsultantProfileSerializer,
)
from authentication.models import PolaUser


class AdminConsultantRegistrationViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing consultant registration requests
    
    Endpoints:
    - GET /admin/consultant-requests/ - List all requests (with filters)
    - GET /admin/consultant-requests/{id}/ - Get request details
    - POST /admin/consultant-requests/{id}/approve/ - Approve request
    - POST /admin/consultant-requests/{id}/reject/ - Reject request
    - GET /admin/consultant-requests/pending/ - List pending requests
    - GET /admin/consultant-requests/statistics/ - Get statistics
    """
    queryset = ConsultantRegistrationRequest.objects.all().select_related(
        'user', 'reviewed_by'
    ).order_by('-created_at')
    serializer_class = ConsultantRegistrationRequestSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by consultant type
        consultant_type = self.request.query_params.get('consultant_type')
        if consultant_type:
            queryset = queryset.filter(consultant_type=consultant_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Search by user name or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a consultant registration request
        Creates ConsultantProfile and activates the consultant
        """
        registration = self.get_object()
        
        if registration.status != 'pending':
            return Response({
                'error': f'Cannot approve {registration.status} request. Only pending requests can be approved.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if consultant profile already exists
        if hasattr(registration.user, 'consultant_profile'):
            return Response({
                'error': 'User already has an active consultant profile'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Approve and create profile
            registration.approve(request.user)
            
            # Get the created profile
            profile = ConsultantProfile.objects.get(user=registration.user)
            
            return Response({
                'success': True,
                'message': f'{registration.user.get_full_name()} has been approved as a consultant',
                'registration': ConsultantRegistrationRequestSerializer(registration, context={'request': request}).data,
                'consultant_profile': ConsultantProfileSerializer(profile, context={'request': request}).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to approve request: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a consultant registration request
        Requires 'reason' in request body
        """
        registration = self.get_object()
        
        if registration.status != 'pending':
            return Response({
                'error': f'Cannot reject {registration.status} request. Only pending requests can be rejected.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason')
        if not reason:
            return Response({
                'error': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Reject with reason
            registration.reject(request.user, reason)
            
            return Response({
                'success': True,
                'message': f'Application from {registration.user.get_full_name()} has been rejected',
                'registration': ConsultantRegistrationRequestSerializer(registration, context={'request': request}).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to reject request: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending consultant registration requests"""
        pending_requests = self.get_queryset().filter(status='pending')
        
        page = self.paginate_queryset(pending_requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pending_requests, many=True)
        return Response({
            'count': pending_requests.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get consultant registration statistics
        """
        total = ConsultantRegistrationRequest.objects.count()
        
        # Count by status
        status_counts = ConsultantRegistrationRequest.objects.aggregate(
            pending=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
            approved=Count(Case(When(status='approved', then=1), output_field=IntegerField())),
            rejected=Count(Case(When(status='rejected', then=1), output_field=IntegerField()))
        )
        
        # Count by consultant type
        type_counts = {}
        for choice in ConsultantRegistrationRequest.CONSULTANT_TYPES:
            type_key = choice[0]
            type_counts[type_key] = ConsultantRegistrationRequest.objects.filter(
                consultant_type=type_key
            ).count()
        
        # Recent requests (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_count = ConsultantRegistrationRequest.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Active consultants
        active_consultants = ConsultantProfile.objects.filter(is_available=True).count()
        total_consultants = ConsultantProfile.objects.count()
        
        return Response({
            'requests': {
                'total': total,
                'pending': status_counts['pending'],
                'approved': status_counts['approved'],
                'rejected': status_counts['rejected'],
                'recent_30_days': recent_count
            },
            'by_type': type_counts,
            'consultants': {
                'total_active': total_consultants,
                'currently_available': active_consultants,
                'unavailable': total_consultants - active_consultants
            }
        })


class AdminConsultantProfileViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing consultant profiles
    
    Endpoints:
    - GET /admin/consultants/ - List all consultants
    - GET /admin/consultants/{id}/ - Get consultant details
    - PATCH /admin/consultants/{id}/ - Update consultant
    - POST /admin/consultants/{id}/toggle_availability/ - Enable/disable availability
    - GET /admin/consultants/statistics/ - Get consultant statistics
    """
    queryset = ConsultantProfile.objects.all().select_related(
        'user', 'registration_request'
    ).order_by('-created_at')
    serializer_class = ConsultantProfileSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by availability
        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        # Filter by consultant type
        consultant_type = self.request.query_params.get('consultant_type')
        if consultant_type:
            queryset = queryset.filter(consultant_type=consultant_type)
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Search by name or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Sort by
        sort_by = self.request.query_params.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """
        Toggle consultant availability (enable/disable)
        """
        consultant = self.get_object()
        new_status = not consultant.is_available
        consultant.is_available = new_status
        consultant.save()
        
        return Response({
            'success': True,
            'message': f'Consultant availability {"enabled" if new_status else "disabled"}',
            'consultant': self.get_serializer(consultant).data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get consultant profile statistics
        """
        total = ConsultantProfile.objects.count()
        available = ConsultantProfile.objects.filter(is_available=True).count()
        
        # Count by type
        type_counts = {}
        for choice in ConsultantProfile.CONSULTANT_TYPES:
            type_key = choice[0]
            type_counts[type_key] = ConsultantProfile.objects.filter(
                consultant_type=type_key
            ).count()
        
        # Service offerings
        mobile_consultations = ConsultantProfile.objects.filter(
            offers_mobile_consultations=True
        ).count()
        physical_consultations = ConsultantProfile.objects.filter(
            offers_physical_consultations=True
        ).count()
        
        # Top consultants by rating
        top_rated = ConsultantProfile.objects.filter(
            total_reviews__gte=5
        ).order_by('-average_rating')[:10]
        
        # Top consultants by consultations
        top_consultants = ConsultantProfile.objects.order_by('-total_consultations')[:10]
        
        return Response({
            'total_consultants': total,
            'available_now': available,
            'unavailable': total - available,
            'by_type': type_counts,
            'service_offerings': {
                'mobile_consultations': mobile_consultations,
                'physical_consultations': physical_consultations
            },
            'top_rated': ConsultantProfileSerializer(top_rated, many=True, context={'request': request}).data,
            'most_active': ConsultantProfileSerializer(top_consultants, many=True, context={'request': request}).data
        })
