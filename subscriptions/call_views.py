"""
Call Management Views
Handles call-related operations including:
- Check user credits before call
- Record call duration and deduct credits
- Get consultant list
- Physical consultation booking
- Call history
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
from decimal import Decimal

from .models import (
    ConsultantProfile,
    UserCallCredit,
    CallSession,
    ConsultationBooking,
    PricingConfiguration,
    ConsultantEarnings,
    CallCreditBundle
)
from .serializers import (
    ConsultantProfileSerializer,
    UserCallCreditSerializer,
    CallSessionSerializer,
    ConsultationBookingSerializer,
)
from authentication.models import PolaUser


# ============================================================================
# CONSULTANT LISTING
# ============================================================================

class ConsultantListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Get list of available consultants
    
    Endpoints:
    - GET /api/v1/calls/consultants/ - List all available consultants
    - GET /api/v1/calls/consultants/{id}/ - Get consultant details
    - GET /api/v1/calls/consultants/search/ - Search by specialization/type
    """
    serializer_class = ConsultantProfileSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return active consultants"""
        queryset = ConsultantProfile.objects.filter(
            is_available=True
        ).select_related('user', 'user__user_role', 'user__contact')
        
        # Apply filters
        consultation_type = self.request.query_params.get('type')  # mobile or physical
        if consultation_type == 'mobile':
            queryset = queryset.filter(offers_mobile_consultations=True)
        elif consultation_type == 'physical':
            queryset = queryset.filter(offers_physical_consultations=True)
        
        # Filter by consultant type (advocate, lawyer, paralegal)
        consultant_type = self.request.query_params.get('consultant_type')
        if consultant_type:
            queryset = queryset.filter(consultant_type=consultant_type)
        
        # Filter by specialization
        specialization = self.request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        
        # Filter by city (for physical consultations)
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                queryset = queryset.filter(average_rating__gte=Decimal(min_rating))
            except (ValueError, TypeError):
                pass
        
        return queryset.order_by('-average_rating', '-total_consultations')
    
    def list(self, request, *args, **kwargs):
        """List consultants with pricing details"""
        queryset = self.filter_queryset(self.get_queryset())
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'consultants': serializer.data,
            'filters': {
                'type': request.query_params.get('type'),
                'consultant_type': request.query_params.get('consultant_type'),
                'specialization': request.query_params.get('specialization'),
                'city': request.query_params.get('city'),
                'min_rating': request.query_params.get('min_rating'),
            }
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search for consultants
        
        Query params:
        - q: Search term (name, specialization)
        - type: mobile or physical
        - consultant_type: advocate, lawyer, paralegal
        - city: City name
        - min_rating: Minimum rating
        """
        queryset = self.get_queryset()
        
        # Text search
        search_query = request.query_params.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(specialization__icontains=search_query)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })


# ============================================================================
# CALL CREDIT MANAGEMENT
# ============================================================================

class CallManagementViewSet(viewsets.ViewSet):
    """
    Manage call credits and call sessions
    
    Endpoints:
    - POST /api/v1/calls/check-credits/ - Check if user has enough credits before call
    - POST /api/v1/calls/record-call/ - Record call duration and deduct credits
    - GET /api/v1/calls/my-credits/ - Get user's available credits
    - GET /api/v1/calls/my-history/ - Get user's call history
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='check-credits')
    def check_credits(self, request):
        """
        Check if user has enough credits to call a consultant
        
        Request body:
        {
            "consultant_id": 123
        }
        
        Response:
        {
            "has_credits": true,
            "available_minutes": 45,
            "consultant": {...},
            "message": "You have 45 minutes available"
        }
        """
        consultant_id = request.data.get('consultant_id')
        
        if not consultant_id:
            return Response(
                {'error': 'consultant_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get consultant
        try:
            consultant = ConsultantProfile.objects.select_related('user').get(id=consultant_id)
        except ConsultantProfile.DoesNotExist:
            return Response(
                {'error': 'Consultant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check consultant availability
        if not consultant.is_available:
            return Response({
                'has_credits': False,
                'error': 'Consultant is not available',
                'consultant': {
                    'id': consultant.id,
                    'name': consultant.user.get_full_name(),
                    'is_available': False
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's active credits
        active_credits = UserCallCredit.objects.filter(
            user=request.user,
            status='active',
            expiry_date__gt=timezone.now(),
            remaining_minutes__gt=0
        ).order_by('expiry_date')  # Use credits expiring soonest first
        
        total_minutes = sum(credit.remaining_minutes for credit in active_credits)
        
        if total_minutes <= 0:
            # Get available bundles to show user
            available_bundles = CallCreditBundle.objects.filter(is_active=True).order_by('price')
            
            bundles_data = [
                {
                    'id': bundle.id,
                    'name': bundle.name,
                    'name_sw': bundle.name_sw,
                    'minutes': bundle.minutes,
                    'price': float(bundle.price),
                    'price_formatted': f"TSh {float(bundle.price):,.0f}",
                    'validity_days': bundle.validity_days,
                    'description': bundle.description,
                }
                for bundle in available_bundles
            ]
            
            return Response({
                'has_credits': False,
                'available_minutes': 0,
                'consultant': {
                    'id': consultant.id,
                    'name': consultant.user.get_full_name(),
                    'consultant_type': consultant.consultant_type,
                    'specialization': consultant.specialization,
                    'rating': float(consultant.average_rating),
                },
                'message': 'You have no available call credits. Please purchase a bundle to continue.',
                'available_bundles': bundles_data,
                'purchase_url': '/api/v1/subscriptions/call-credits/purchase/'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        return Response({
            'has_credits': True,
            'available_minutes': total_minutes,
            'active_credits_count': active_credits.count(),
            'consultant': {
                'id': consultant.id,
                'name': consultant.user.get_full_name(),
                'consultant_type': consultant.consultant_type,
                'specialization': consultant.specialization,
                'rating': float(consultant.average_rating),
                'years_of_experience': consultant.years_of_experience,
            },
            'credits_breakdown': [
                {
                    'id': credit.id,
                    'remaining_minutes': credit.remaining_minutes,
                    'expires_at': credit.expiry_date,
                    'bundle_name': credit.bundle.name if credit.bundle else 'Unknown'
                }
                for credit in active_credits
            ],
            'message': f'You have {total_minutes} minutes available. You can start the call.'
        })
    
    @action(detail=False, methods=['post'], url_path='record-call')
    def record_call(self, request):
        """
        Record call duration and deduct credits
        Called by the app after call ends
        
        Request body:
        {
            "consultant_id": 123,
            "duration_seconds": 420
        }
        
        Response:
        {
            "success": true,
            "call_session": {...},
            "credits_deducted": 7,
            "remaining_minutes": 38,
            "message": "Call recorded successfully. 7 minutes deducted."
        }
        """
        consultant_id = request.data.get('consultant_id')
        duration_seconds = request.data.get('duration_seconds')
        
        # Validation
        if not consultant_id or duration_seconds is None:
            return Response(
                {'error': 'consultant_id and duration_seconds are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            duration_seconds = int(duration_seconds)
        except (ValueError, TypeError):
            return Response(
                {'error': 'duration_seconds must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if duration_seconds < 0:
            return Response(
                {'error': 'duration_seconds cannot be negative'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Security check: Max duration 4 hours
        if duration_seconds > 14400:  # 4 hours
            return Response(
                {'error': 'Duration exceeds maximum allowed (4 hours)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get consultant
        try:
            consultant = ConsultantProfile.objects.select_related('user').get(id=consultant_id)
        except ConsultantProfile.DoesNotExist:
            return Response(
                {'error': 'Consultant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Convert seconds to minutes (round up)
        duration_minutes = (duration_seconds + 59) // 60  # Round up
        
        # Minimum billable duration: 1 minute
        if duration_minutes < 1:
            duration_minutes = 1
        
        # Get user's active credits (oldest expiring first)
        active_credits = UserCallCredit.objects.filter(
            user=request.user,
            status='active',
            expiry_date__gt=timezone.now(),
            remaining_minutes__gt=0
        ).order_by('expiry_date')
        
        total_available = sum(credit.remaining_minutes for credit in active_credits)
        
        if total_available < duration_minutes:
            return Response({
                'error': 'Insufficient credits',
                'required_minutes': duration_minutes,
                'available_minutes': total_available,
                'message': f'You need {duration_minutes} minutes but only have {total_available} minutes available.'
            }, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # Deduct credits from multiple bundles if needed
        with db_transaction.atomic():
            remaining_to_deduct = duration_minutes
            credits_used = []
            
            for credit in active_credits:
                if remaining_to_deduct <= 0:
                    break
                
                if credit.remaining_minutes >= remaining_to_deduct:
                    # This credit has enough minutes
                    credit.remaining_minutes -= remaining_to_deduct
                    credits_used.append({
                        'credit_id': credit.id,
                        'minutes_deducted': remaining_to_deduct
                    })
                    remaining_to_deduct = 0
                    
                    if credit.remaining_minutes == 0:
                        credit.status = 'depleted'
                    
                    credit.save()
                else:
                    # Use all remaining minutes from this credit
                    deducted = credit.remaining_minutes
                    remaining_to_deduct -= deducted
                    credits_used.append({
                        'credit_id': credit.id,
                        'minutes_deducted': deducted
                    })
                    
                    credit.remaining_minutes = 0
                    credit.status = 'depleted'
                    credit.save()
            
            # Create call session record
            call_session = CallSession.objects.create(
                booking=None,  # Simplified - no booking required for mobile calls
                call_credit=active_credits.first() if active_credits.exists() else None,
                start_time=timezone.now() - timedelta(seconds=duration_seconds),
                end_time=timezone.now(),
                duration_minutes=duration_minutes
            )
            
            # Update consultant stats
            consultant.total_consultations += 1
            consultant.save()
            
            # Calculate earnings (50/50 split for mobile calls)
            # Rate: ~456 TZS per minute (based on 5 min = 3000 TZS)
            rate_per_minute = Decimal('450.00')
            gross_amount = rate_per_minute * duration_minutes
            platform_commission = gross_amount * Decimal('0.50')
            consultant_earnings = gross_amount * Decimal('0.50')
            
            # Record consultant earnings
            # Note: We create a simplified booking record for earnings tracking
            simplified_booking = ConsultationBooking.objects.create(
                client=request.user,
                consultant=consultant.user,
                booking_type='mobile',
                status='completed',
                scheduled_date=timezone.now(),
                scheduled_duration_minutes=duration_minutes,
                actual_start_time=call_session.start_time,
                actual_end_time=call_session.end_time,
                actual_duration_minutes=duration_minutes,
                total_amount=gross_amount,
                platform_commission=platform_commission,
                consultant_earnings=consultant_earnings,
            )
            
            # Link call session to booking
            call_session.booking = simplified_booking
            call_session.save()
            
            # Create earnings record
            ConsultantEarnings.objects.create(
                consultant=consultant.user,
                booking=simplified_booking,
                service_type='mobile_consultation',
                gross_amount=gross_amount,
                platform_commission=platform_commission,
                net_earnings=consultant_earnings
            )
            
            # Update consultant's total earnings
            consultant.total_earnings += consultant_earnings
            consultant.save()
        
        # Get remaining credits
        remaining_credits = UserCallCredit.objects.filter(
            user=request.user,
            status='active',
            expiry_date__gt=timezone.now(),
            remaining_minutes__gt=0
        )
        total_remaining = sum(credit.remaining_minutes for credit in remaining_credits)
        
        return Response({
            'success': True,
            'call_session': {
                'id': call_session.id,
                'duration_minutes': duration_minutes,
                'duration_seconds': duration_seconds,
                'start_time': call_session.start_time,
                'end_time': call_session.end_time,
            },
            'consultant': {
                'id': consultant.id,
                'name': consultant.user.get_full_name(),
            },
            'credits_deducted': duration_minutes,
            'credits_used': credits_used,
            'remaining_minutes': total_remaining,
            'earnings': {
                'gross_amount': float(gross_amount),
                'consultant_earnings': float(consultant_earnings),
                'platform_commission': float(platform_commission),
            },
            'message': f'Call recorded successfully. {duration_minutes} minutes deducted. You have {total_remaining} minutes remaining.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my-credits')
    def my_credits(self, request):
        """
        Get user's available call credits
        
        Response:
        {
            "total_minutes": 45,
            "active_credits": [...],
            "expired_credits": [...]
        }
        """
        # Active credits
        active_credits = UserCallCredit.objects.filter(
            user=request.user,
            status='active',
            expiry_date__gt=timezone.now(),
            remaining_minutes__gt=0
        ).select_related('bundle').order_by('expiry_date')
        
        # Recently expired credits (last 30 days)
        expired_credits = UserCallCredit.objects.filter(
            user=request.user,
            status='expired',
            expiry_date__gte=timezone.now() - timedelta(days=30)
        ).select_related('bundle').order_by('-expiry_date')[:5]
        
        total_minutes = sum(credit.remaining_minutes for credit in active_credits)
        
        return Response({
            'total_minutes': total_minutes,
            'active_credits_count': active_credits.count(),
            'active_credits': [
                {
                    'id': credit.id,
                    'bundle_name': credit.bundle.name if credit.bundle else 'Unknown',
                    'total_minutes': credit.total_minutes,
                    'remaining_minutes': credit.remaining_minutes,
                    'used_minutes': credit.total_minutes - credit.remaining_minutes,
                    'purchase_date': credit.purchase_date,
                    'expiry_date': credit.expiry_date,
                    'days_until_expiry': (credit.expiry_date - timezone.now()).days,
                }
                for credit in active_credits
            ],
            'expired_credits': [
                {
                    'id': credit.id,
                    'bundle_name': credit.bundle.name if credit.bundle else 'Unknown',
                    'total_minutes': credit.total_minutes,
                    'remaining_minutes': credit.remaining_minutes,
                    'expired_date': credit.expiry_date,
                }
                for credit in expired_credits
            ],
            'bundles_url': '/api/v1/subscriptions/call-credits/bundles/'
        })
    
    @action(detail=False, methods=['get'], url_path='my-history')
    def my_history(self, request):
        """
        Get user's call history
        
        Query params:
        - limit: Number of records (default: 20)
        - offset: Pagination offset
        """
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        # Get call sessions for user's bookings
        call_sessions = CallSession.objects.filter(
            booking__client=request.user
        ).select_related(
            'booking__consultant',
            'call_credit__bundle'
        ).order_by('-start_time')[offset:offset+limit]
        
        total_count = CallSession.objects.filter(
            booking__client=request.user
        ).count()
        
        # Calculate stats
        total_minutes_used = CallSession.objects.filter(
            booking__client=request.user
        ).aggregate(total=Count('duration_minutes'))['total'] or 0
        
        return Response({
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'total_minutes_used': total_minutes_used,
            'calls': [
                {
                    'id': call.id,
                    'consultant': {
                        'name': call.booking.consultant.get_full_name() if call.booking and call.booking.consultant else 'Unknown',
                    },
                    'duration_minutes': call.duration_minutes,
                    'start_time': call.start_time,
                    'end_time': call.end_time,
                    'date': call.start_time.date(),
                    'call_quality_rating': call.call_quality_rating,
                }
                for call in call_sessions
            ]
        })


# ============================================================================
# PHYSICAL CONSULTATION BOOKING
# ============================================================================

class PhysicalConsultationViewSet(viewsets.ViewSet):
    """
    Book physical consultations with consultants
    
    Endpoints:
    - POST /api/v1/calls/book-physical/ - Book a physical consultation
    - GET /api/v1/calls/my-bookings/ - Get user's bookings
    - GET /api/v1/calls/my-bookings/{id}/ - Get booking details
    - PATCH /api/v1/calls/my-bookings/{id}/cancel/ - Cancel booking
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='book-physical')
    def book_physical(self, request):
        """
        Book a physical consultation
        
        Request body:
        {
            "consultant_id": 123,
            "scheduled_date": "2025-12-10",
            "scheduled_time": "14:00:00",
            "duration_minutes": 60,
            "client_notes": "Need advice on property dispute"
        }
        
        Response:
        {
            "success": true,
            "booking": {...},
            "payment_required": true,
            "amount": 50000,
            "message": "Booking created. Awaiting payment."
        }
        """
        consultant_id = request.data.get('consultant_id')
        scheduled_date = request.data.get('scheduled_date')
        scheduled_time = request.data.get('scheduled_time')
        duration_minutes = request.data.get('duration_minutes', 60)
        client_notes = request.data.get('client_notes', '')
        
        # Validation
        if not consultant_id or not scheduled_date or not scheduled_time:
            return Response(
                {'error': 'consultant_id, scheduled_date, and scheduled_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get consultant
        try:
            consultant = ConsultantProfile.objects.select_related('user').get(id=consultant_id)
        except ConsultantProfile.DoesNotExist:
            return Response(
                {'error': 'Consultant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if consultant offers physical consultations
        if not consultant.offers_physical_consultations:
            return Response({
                'error': 'This consultant does not offer physical consultations',
                'consultant': {
                    'id': consultant.id,
                    'name': consultant.user.get_full_name(),
                    'offers_mobile': consultant.offers_mobile_consultations,
                    'offers_physical': consultant.offers_physical_consultations,
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get pricing for physical consultation
        try:
            pricing = PricingConfiguration.objects.get(
                service_type=f'PHYSICAL_{consultant.consultant_type.upper()}',
                is_active=True
            )
        except PricingConfiguration.DoesNotExist:
            return Response(
                {'error': 'Pricing not configured for this consultant type'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Calculate amounts
        total_amount = pricing.price
        platform_commission = total_amount * (pricing.platform_commission_percent / Decimal('100'))
        consultant_earnings = total_amount * (pricing.consultant_share_percent / Decimal('100'))
        
        # Parse datetime
        from datetime import datetime
        try:
            scheduled_datetime = datetime.strptime(
                f"{scheduled_date} {scheduled_time}",
                "%Y-%m-%d %H:%M:%S"
            )
            scheduled_datetime = timezone.make_aware(scheduled_datetime)
        except ValueError:
            return Response(
                {'error': 'Invalid date/time format. Use YYYY-MM-DD for date and HH:MM:SS for time'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if datetime is in the future
        if scheduled_datetime <= timezone.now():
            return Response(
                {'error': 'Scheduled date/time must be in the future'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create booking
        with db_transaction.atomic():
            booking = ConsultationBooking.objects.create(
                client=request.user,
                consultant=consultant.user,
                booking_type='physical',
                status='pending',
                scheduled_date=scheduled_datetime,
                scheduled_duration_minutes=duration_minutes,
                total_amount=total_amount,
                platform_commission=platform_commission,
                consultant_earnings=consultant_earnings,
                client_notes=client_notes,
                meeting_location=consultant.city,  # Default to consultant's city
            )
        
        return Response({
            'success': True,
            'booking': {
                'id': booking.id,
                'consultant': {
                    'id': consultant.id,
                    'name': consultant.user.get_full_name(),
                    'consultant_type': consultant.consultant_type,
                    'city': consultant.city,
                },
                'scheduled_date': booking.scheduled_date,
                'duration_minutes': booking.scheduled_duration_minutes,
                'status': booking.status,
                'meeting_location': booking.meeting_location,
                'client_notes': booking.client_notes,
            },
            'payment_required': True,
            'amount': float(total_amount),
            'currency': 'TZS',
            'pricing_breakdown': {
                'total': float(total_amount),
                'platform_commission': float(platform_commission),
                'consultant_earnings': float(consultant_earnings),
                'split': f'{pricing.platform_commission_percent}% Platform / {pricing.consultant_share_percent}% Consultant'
            },
            'message': f'Physical consultation booked for {scheduled_datetime.strftime("%B %d, %Y at %I:%M %p")}. Please complete payment to confirm.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my-bookings')
    def my_bookings(self, request):
        """
        Get user's consultation bookings
        
        Query params:
        - status: Filter by status (pending, confirmed, completed, cancelled)
        - type: Filter by type (mobile, physical)
        """
        queryset = ConsultationBooking.objects.filter(
            client=request.user
        ).select_related('consultant').order_by('-scheduled_date')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        type_filter = request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(booking_type=type_filter)
        
        serializer = ConsultationBookingSerializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'bookings': serializer.data
        })
