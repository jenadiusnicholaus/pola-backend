"""
Admin Consultation Management Views
Handles pricing configs, consultant profiles, and physical bookings
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import timedelta
from decimal import Decimal

from .models import (
    PricingConfiguration, ConsultantProfile, ConsultationBooking,
    ConsultantEarnings, PaymentTransaction
)
from .admin_consultation_serializers import (
    PricingConfigurationAdminSerializer,
    ConsultantProfileAdminSerializer,
    ConsultationBookingAdminSerializer,
    UpdateBookingStatusSerializer,
    ConsultationStatsSerializer
)


class PricingConfigurationViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing consultation pricing configurations
    
    Endpoints:
    - GET    /admin/consultations/pricing/          - List all configs
    - POST   /admin/consultations/pricing/          - Create config
    - GET    /admin/consultations/pricing/{id}/     - Get config details
    - PUT    /admin/consultations/pricing/{id}/     - Update config
    - DELETE /admin/consultations/pricing/{id}/     - Delete config
    """
    queryset = PricingConfiguration.objects.all()
    serializer_class = PricingConfigurationAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by service_type (instead of consultation_type)
        service_type = self.request.query_params.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('service_type')


class ConsultantProfileViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing consultant profiles
    
    Endpoints:
    - GET    /admin/consultations/consultants/          - List all consultants
    - POST   /admin/consultations/consultants/          - Create consultant
    - GET    /admin/consultations/consultants/{id}/     - Get consultant details
    - PUT    /admin/consultations/consultants/{id}/     - Update consultant
    - DELETE /admin/consultations/consultants/{id}/     - Delete consultant
    - POST   /admin/consultations/consultants/{id}/toggle-availability/  - Toggle availability
    """
    queryset = ConsultantProfile.objects.all()
    serializer_class = ConsultantProfileAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by availability
        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        # Filter by specialization
        specialization = self.request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'], url_path='toggle-availability')
    def toggle_availability(self, request, pk=None):
        """Toggle consultant availability"""
        consultant = self.get_object()
        is_available = request.data.get('is_available', not consultant.is_available)
        
        consultant.is_available = is_available
        consultant.save()
        
        return Response({
            'success': True,
            'message': f"Consultant {'available' if is_available else 'unavailable'} now",
            'consultant': ConsultantProfileAdminSerializer(consultant).data
        })
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Get all bookings for a consultant"""
        consultant = self.get_object()
        bookings = ConsultationBooking.objects.filter(consultant=consultant.user).order_by('-created_at')
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = ConsultationBookingAdminSerializer(bookings[start:end], many=True)
        
        return Response({
            'count': bookings.count(),
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def earnings(self, request, pk=None):
        """Get earnings breakdown for a consultant"""
        consultant = self.get_object()
        
        earnings = ConsultantEarnings.objects.filter(consultant=consultant.user)
        
        total_earnings = earnings.aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
        
        # Earnings by month (last 12 months)
        now = timezone.now()
        monthly_earnings = {}
        for i in range(12):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            if i == 0:
                month_end = now
            else:
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end.replace(day=1, hour=0, minute=0, second=0) - timedelta(seconds=1)
            
            month_key = month_start.strftime('%Y-%m')
            month_total = earnings.filter(
                booking__created_at__gte=month_start,
                booking__created_at__lte=month_end
            ).aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
            
            monthly_earnings[month_key] = month_total
        
        return Response({
            'consultant_id': consultant.id,
            'total_earnings': total_earnings,
            'monthly_earnings': monthly_earnings,
            'total_bookings': ConsultationBooking.objects.filter(
                consultant=consultant.user, status='completed'
            ).count()
        })


class ConsultationBookingViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing consultation bookings
    
    Endpoints:
    - GET    /admin/consultations/bookings/          - List all bookings
    - POST   /admin/consultations/bookings/          - Create booking
    - GET    /admin/consultations/bookings/{id}/     - Get booking details
    - PUT    /admin/consultations/bookings/{id}/     - Update booking
    - DELETE /admin/consultations/bookings/{id}/     - Delete booking
    - POST   /admin/consultations/bookings/{id}/update-status/  - Update status
    - GET    /admin/consultations/stats/             - Statistics
    - GET    /admin/consultations/revenue/           - Revenue reports
    """
    queryset = ConsultationBooking.objects.all()
    serializer_class = ConsultationBookingAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by consultant
        consultant_id = self.request.query_params.get('consultant_id')
        if consultant_id:
            queryset = queryset.filter(consultant_id=consultant_id)
        
        # Filter by client
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by booking type
        booking_type = self.request.query_params.get('booking_type')
        if booking_type:
            queryset = queryset.filter(booking_type=booking_type)
        
        # Filter by date range (use scheduled_date instead of booking_date)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update booking status"""
        booking = self.get_object()
        serializer = UpdateBookingStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            admin_note = serializer.validated_data.get('admin_note', '')
            
            old_status = booking.status
            booking.status = new_status
            
            # If status is completed, record earnings
            if new_status == 'completed' and old_status != 'completed':
                # Determine service type and commission split
                if booking.booking_type == 'mobile':
                    # Mobile: 50/50 split
                    platform_commission = booking.total_amount * Decimal('0.50')
                    consultant_share = booking.total_amount * Decimal('0.50')
                else:  # physical
                    # Physical: 60/40 split
                    platform_commission = booking.total_amount * Decimal('0.60')
                    consultant_share = booking.total_amount * Decimal('0.40')
                
                # Create consultant earnings record
                ConsultantEarnings.objects.get_or_create(
                    consultant=booking.consultant,
                    booking=booking,
                    defaults={
                        'service_type': booking.booking_type,
                        'gross_amount': booking.total_amount,
                        'platform_commission': platform_commission,
                        'net_earnings': consultant_share,
                        'paid_out': False
                    }
                )
            
            booking.save()
            
            return Response({
                'success': True,
                'message': f"Booking status updated from {old_status} to {new_status}",
                'admin_note': admin_note,
                'booking': ConsultationBookingAdminSerializer(booking).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get consultation statistics"""
        # Pricing configs
        total_pricing_configs = PricingConfiguration.objects.count()
        
        # Consultants
        total_consultants = ConsultantProfile.objects.count()
        active_consultants = ConsultantProfile.objects.filter(is_available=True).count()
        
        # Bookings
        all_bookings = ConsultationBooking.objects.all()
        total_bookings = all_bookings.count()
        pending_bookings = all_bookings.filter(status='pending').count()
        confirmed_bookings = all_bookings.filter(status='confirmed').count()
        completed_bookings = all_bookings.filter(status='completed').count()
        cancelled_bookings = all_bookings.filter(status='cancelled').count()
        
        # Revenue - sum from completed bookings
        completed_bookings_qs = ConsultationBooking.objects.filter(status='completed')
        total_revenue = sum(b.total_amount for b in completed_bookings_qs)
        
        # Calculate platform and consultant earnings
        total_platform_earnings = sum(b.platform_commission for b in completed_bookings_qs)
        total_consultant_earnings = sum(b.consultant_earnings for b in completed_bookings_qs)
        
        # Hours/Minutes
        completed = ConsultationBooking.objects.filter(status='completed')
        total_consultation_minutes = sum(b.actual_duration_minutes for b in completed)
        average_consultation_minutes = (
            total_consultation_minutes / completed.count()
        ) if completed.count() > 0 else 0
        
        # Ratings - ConsultationBooking model doesn't have rating field, remove it
        average_rating = Decimal('0')
        
        stats = {
            'total_pricing_configs': total_pricing_configs,
            'total_consultants': total_consultants,
            'active_consultants': active_consultants,
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'confirmed_bookings': confirmed_bookings,
            'completed_bookings': completed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'total_revenue': Decimal(str(total_revenue)),
            'total_platform_earnings': Decimal(str(total_platform_earnings)),
            'total_consultant_earnings': Decimal(str(total_consultant_earnings)),
            'total_consultation_hours': round(Decimal(total_consultation_minutes) / 60, 2),
            'average_consultation_hours': round(Decimal(average_consultation_minutes) / 60, 2),
            'average_rating': average_rating
        }
        
        serializer = ConsultationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue reports over time"""
        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, yearly
        
        now = timezone.now()
        
        if period == 'weekly':
            start_date = now - timedelta(weeks=12)
        elif period == 'monthly':
            start_date = now - timedelta(days=365)
        elif period == 'yearly':
            start_date = now - timedelta(days=365 * 3)
        else:  # daily
            start_date = now - timedelta(days=30)
        
        # Get all completed bookings in period
        bookings = ConsultationBooking.objects.filter(
            status='completed',
            created_at__gte=start_date
        ).order_by('created_at')
        
        # Group by period
        revenue_data = {}
        for booking in bookings:
            if period == 'weekly':
                key = f"{booking.created_at.year}-W{booking.created_at.isocalendar()[1]}"
            elif period == 'monthly':
                key = booking.created_at.strftime('%Y-%m')
            elif period == 'yearly':
                key = str(booking.created_at.year)
            else:  # daily
                key = booking.created_at.strftime('%Y-%m-%d')
            
            if key not in revenue_data:
                revenue_data[key] = {
                    'period': key,
                    'total_revenue': Decimal('0'),
                    'platform_earnings': Decimal('0'),
                    'consultant_earnings': Decimal('0'),
                    'total_bookings': 0
                }
            
            revenue_data[key]['total_revenue'] += booking.total_amount
            revenue_data[key]['platform_earnings'] += booking.platform_commission
            revenue_data[key]['consultant_earnings'] += booking.consultant_earnings
            revenue_data[key]['total_bookings'] += 1
        
        return Response({
            'period': period,
            'data': list(revenue_data.values())
        })
