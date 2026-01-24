"""
Physical Consultation Booking Views
Handles booking, managing, and processing physical in-person consultations
"""
from django.db import transaction as db_transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
import uuid
from notification.notification_service import notification_service

from .models import (
    ConsultationBooking,
    ConsultantProfile,
    PaymentTransaction,
    PricingConfiguration,
    ConsultantEarnings
)
from .serializers import (
    ConsultationBookingSerializer,
    ConsultationBookingCreateSerializer
)
from .azampay_integration import azampay_client, AzamPayError, format_phone_number, detect_mobile_provider


class PhysicalConsultationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing physical consultation bookings
    
    Endpoints:
    - POST /api/v1/consultations/physical/book/ - Book a physical consultation
    - GET /api/v1/consultations/physical/ - List user's physical consultations
    - GET /api/v1/consultations/physical/{id}/ - Get booking details
    - PATCH /api/v1/consultations/physical/{id}/cancel/ - Cancel a booking
    - PATCH /api/v1/consultations/physical/{id}/confirm/ - Confirm a booking (consultant only)
    - POST /api/v1/consultations/physical/{id}/start/ - Start consultation session
    - POST /api/v1/consultations/physical/{id}/complete/ - Complete consultation session
    - POST /api/v1/consultations/physical/{id}/reschedule/ - Reschedule consultation
    - GET /api/v1/consultations/physical/upcoming/ - Get upcoming consultations
    - GET /api/v1/consultations/physical/history/ - Get consultation history
    """
    serializer_class = ConsultationBookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return physical consultation bookings for current user"""
        user = self.request.user
        
        # Return bookings where user is either client or consultant (physical only)
        return ConsultationBooking.objects.filter(
            Q(client=user) | Q(consultant=user),
            booking_type='physical'
        ).select_related(
            'client', 'consultant'
        ).order_by('-scheduled_date')
    
    @action(detail=False, methods=['post'])
    def book(self, request):
        """
        Step 1: Create a new physical consultation booking (no payment yet)
        
        Request body:
        {
            "consultant_id": 123,
            "scheduled_date": "2025-12-25T14:00:00Z",
            "scheduled_duration_minutes": 60,
            "meeting_location": "Consultant's Office, Dar es Salaam",
            "client_notes": "Need legal advice on property matters"
        }
        
        Response includes payment_info for next step (pay endpoint)
        """
        from subscriptions.permissions import check_subscription_permission
        
        # Check if user can book consultations (Free trial users cannot)
        if not check_subscription_permission(request.user, 'can_book_consultation'):
            return Response({
                'error': 'Subscription required',
                'message': 'Free trial users cannot book consultations. Please subscribe to access this feature.',
                'message_sw': 'Watumiaji wa majaribio ya bure hawawezi kuweka nafasi ya kushauriana. Tafadhali jiandikishe kufikia kipengele hiki.',
                'upgrade_required': True,
                'restriction': 'book_consultation'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ConsultationBookingCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        consultant_profile = validated_data['consultant_profile']
        
        # Get pricing configuration for physical consultation
        try:
            pricing_config = PricingConfiguration.objects.get(
                service_type='PHYSICAL_CONSULTATION',
                is_active=True
            )
        except PricingConfiguration.DoesNotExist:
            # Fallback to any physical pricing or create default
            pricing_config = PricingConfiguration.objects.filter(
                service_type__startswith='PHYSICAL',
                is_active=True
            ).first()
            if not pricing_config:
                return Response(
                    {'error': 'Pricing configuration not found. Please contact support.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Calculate pricing
        base_rate = pricing_config.price  # Price per 30 minutes
        duration_minutes = validated_data.get('scheduled_duration_minutes', 30)
        
        # Calculate total amount (base rate per 30 minutes)
        total_amount = (base_rate / 30) * duration_minutes
        
        # Apply consultant multiplier if they have custom pricing
        if hasattr(consultant_profile, 'pricing_multiplier') and consultant_profile.pricing_multiplier:
            total_amount *= Decimal(str(consultant_profile.pricing_multiplier))
        
        # Calculate platform commission
        commission_percentage = pricing_config.platform_commission_percent
        platform_commission = total_amount * (commission_percentage / 100)
        consultant_earnings = total_amount - platform_commission
        
        # Create booking only (no payment transaction yet)
        try:
            with db_transaction.atomic():
                # Create booking with status=pending
                booking = ConsultationBooking.objects.create(
                    client=request.user,
                    consultant=consultant_profile.user,
                    booking_type='physical',
                    status='pending',
                    scheduled_date=validated_data['scheduled_date'],
                    scheduled_duration_minutes=duration_minutes,
                    total_amount=total_amount,
                    platform_commission=platform_commission,
                    consultant_earnings=consultant_earnings,
                    meeting_location=validated_data.get('meeting_location', ''),
                    client_notes=validated_data.get('client_notes', '')
                )
                
                # Send notification to consultant
                try:
                    notification_service.send_consultation_request_notification(
                        consultant=consultant_profile.user,
                        client=request.user,
                        booking_id=booking.id,
                        consultation_type='physical',
                        scheduled_date=booking.scheduled_date.strftime('%B %d, %Y'),
                        scheduled_time=booking.scheduled_date.strftime('%I:%M %p')
                    )
                except Exception as e:
                    # Log but don't fail the booking
                    import logging
                    logging.getLogger(__name__).error(f"Failed to send booking notification: {str(e)}")
                
                return Response({
                    'success': True,
                    'message': 'Booking created successfully. Proceed to payment to confirm.',
                    'booking': ConsultationBookingSerializer(booking).data,
                    'payment_info': {
                        'payment_category': 'consultation',
                        'item_id': booking.id,
                        'amount': float(total_amount),
                        'currency': 'TZS',
                        'consultant_name': consultant_profile.user.get_full_name(),
                        'scheduled_date': booking.scheduled_date.isoformat(),
                        'duration_minutes': duration_minutes,
                        'meeting_location': booking.meeting_location,
                    },
                    'next_step': {
                        'endpoint': '/api/v1/subscriptions/unified-payments/initiate/',
                        'method': 'POST',
                        'body': {
                            'payment_category': 'consultation',
                            'item_id': booking.id,
                            'phone_number': '<your_phone_number>',
                            'payment_method': 'mobile_money',
                            'provider': 'Mpesa'  # or Airtel, Tigo
                        }
                    }
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to create booking: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """
        Step 2: Initiate payment for a pending booking
        
        Request body:
        {
            "phone_number": "0712345678",
            "payment_method": "mobile_money"  // optional, defaults to mobile_money
        }
        
        Uses unified payment API to process payment via AzamPay
        """
        from .payment_service import payment_service, PaymentServiceError
        
        booking = self.get_object()
        
        # Verify user owns this booking
        if booking.client != request.user:
            return Response(
                {'error': 'You can only pay for your own bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check booking is still pending
        if booking.status == 'confirmed':
            return Response(
                {'error': 'This booking is already confirmed and paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.status == 'cancelled':
            return Response(
                {'error': 'This booking has been cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if there's already a completed payment
        existing_payment = PaymentTransaction.objects.filter(
            related_booking=booking,
            status='completed'
        ).first()
        
        if existing_payment:
            return Response(
                {'error': 'Payment already completed for this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get payment details from request
        phone_number = request.data.get('phone_number')
        payment_method = request.data.get('payment_method', 'mobile_money')
        
        if not phone_number:
            return Response(
                {'error': 'phone_number is required for payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use unified payment service
            result = payment_service.initiate_payment(
                user=request.user,
                payment_category='consultation',
                item_id=booking.id,
                payment_method=payment_method,
                phone_number=phone_number,
            )
            
            if result['success']:
                # Get formatted phone and provider for response
                formatted_phone = format_phone_number(phone_number)
                provider = detect_mobile_provider(formatted_phone)
                
                return Response({
                    'success': True,
                    'message': 'Payment initiated. Complete payment on your phone to confirm booking.',
                    'booking': ConsultationBookingSerializer(booking).data,
                    'payment': {
                        'transaction_id': result['transaction'].id,
                        'reference': result['transaction'].payment_reference,
                        'amount': float(booking.total_amount),
                        'currency': 'TZS',
                        'status': result['transaction'].status,
                        'gateway_transaction_id': result['payment_details'].get('transaction_id'),
                        'provider': provider,
                        'phone': formatted_phone,
                    },
                    'next_step': f'Complete payment on your {provider} phone: {formatted_phone}'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': result.get('message', 'Payment initiation failed'),
                    'booking': ConsultationBookingSerializer(booking).data,
                    'error': result.get('message')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except PaymentServiceError as e:
            return Response({
                'success': False,
                'error': str(e),
                'booking': ConsultationBookingSerializer(booking).data,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Payment initiation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
        """
        Confirm a physical consultation booking (Consultant only)
        """
        booking = self.get_object()
        
        # Check if user is the consultant
        if booking.consultant != request.user:
            return Response(
                {'error': 'Only the assigned consultant can confirm this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking is in pending state
        if booking.status != 'pending':
            return Response(
                {'error': f'Cannot confirm booking with status: {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment is completed
        payment = PaymentTransaction.objects.filter(
            related_booking=booking,
            status='success'
        ).first()
        
        if not payment:
            return Response(
                {'error': 'Cannot confirm booking. Payment not completed yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.confirm_booking()
        
        return Response({
            'success': True,
            'message': 'Consultation confirmed successfully',
            'booking': ConsultationBookingSerializer(booking).data
        })
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start the physical consultation session (Consultant only)
        """
        booking = self.get_object()
        
        # Check if user is the consultant
        if booking.consultant != request.user:
            return Response(
                {'error': 'Only the assigned consultant can start this session'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking is confirmed
        if booking.status != 'confirmed':
            return Response(
                {'error': f'Cannot start consultation with status: {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.start_session()
        
        return Response({
            'success': True,
            'message': 'Consultation session started',
            'booking': ConsultationBookingSerializer(booking).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete the physical consultation session (Consultant only)
        
        Request body (optional):
        {
            "consultant_notes": "Session notes and recommendations"
        }
        """
        booking = self.get_object()
        
        # Check if user is the consultant
        if booking.consultant != request.user:
            return Response(
                {'error': 'Only the assigned consultant can complete this session'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking is in progress
        if booking.status != 'in_progress':
            return Response(
                {'error': f'Cannot complete consultation with status: {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add consultant notes if provided
        consultant_notes = request.data.get('consultant_notes', '')
        if consultant_notes:
            booking.consultant_notes = consultant_notes
        
        booking.complete_session()
        
        return Response({
            'success': True,
            'message': 'Consultation completed successfully',
            'booking': ConsultationBookingSerializer(booking).data,
            'earnings': {
                'total_amount': float(booking.total_amount),
                'platform_commission': float(booking.platform_commission),
                'consultant_earnings': float(booking.consultant_earnings)
            }
        })
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """
        Cancel a physical consultation booking
        
        Request body:
        {
            "reason": "Reason for cancellation"
        }
        """
        booking = self.get_object()
        
        # Check if user is client or consultant
        if booking.client != request.user and booking.consultant != request.user:
            return Response(
                {'error': 'You do not have permission to cancel this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking can be cancelled
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel booking with status: {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if session has started
        if booking.status == 'in_progress':
            return Response(
                {'error': 'Cannot cancel a consultation that is already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        booking.status = 'cancelled'
        if reason:
            booking.consultant_notes = f"Cancelled by {request.user.get_full_name()}: {reason}"
        booking.save()
        
        # Handle refund if payment was made
        payment = PaymentTransaction.objects.filter(
            related_booking=booking,
            status='success'
        ).first()
        
        if payment:
            # Create refund transaction (actual refund processing would be handled separately)
            refund_amount = booking.total_amount
            # TODO: Process actual refund through payment gateway
            
            return Response({
                'success': True,
                'message': 'Booking cancelled successfully. Refund will be processed.',
                'booking': ConsultationBookingSerializer(booking).data,
                'refund_info': {
                    'amount': float(refund_amount),
                    'status': 'pending',
                    'note': 'Refund will be processed within 3-5 business days'
                }
            })
        
        return Response({
            'success': True,
            'message': 'Booking cancelled successfully',
            'booking': ConsultationBookingSerializer(booking).data
        })
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """
        Reschedule a physical consultation
        
        Request body:
        {
            "new_scheduled_date": "2025-12-26T15:00:00Z",
            "reason": "Reason for rescheduling"
        }
        """
        booking = self.get_object()
        
        # Check if user is client or consultant
        if booking.client != request.user and booking.consultant != request.user:
            return Response(
                {'error': 'You do not have permission to reschedule this booking'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking can be rescheduled
        if booking.status in ['completed', 'cancelled', 'in_progress']:
            return Response(
                {'error': f'Cannot reschedule booking with status: {booking.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_date_str = request.data.get('new_scheduled_date')
        if not new_date_str:
            return Response(
                {'error': 'new_scheduled_date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils.dateparse import parse_datetime
        new_date = parse_datetime(new_date_str)
        
        if not new_date:
            return Response(
                {'error': 'Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new date is in the future
        if new_date <= timezone.now():
            return Response(
                {'error': 'New scheduled date must be in the future'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_date = booking.scheduled_date
        booking.scheduled_date = new_date
        booking.status = 'pending'  # Reset to pending for consultant to confirm
        
        reason = request.data.get('reason', '')
        if reason:
            note = f"Rescheduled from {old_date.strftime('%Y-%m-%d %H:%M')} by {request.user.get_full_name()}: {reason}"
            booking.consultant_notes = booking.consultant_notes + "\n" + note if booking.consultant_notes else note
        
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Consultation rescheduled successfully',
            'booking': ConsultationBookingSerializer(booking).data,
            'old_date': old_date.isoformat(),
            'new_date': new_date.isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming physical consultations for the user"""
        queryset = self.get_queryset().filter(
            scheduled_date__gte=timezone.now(),
            status__in=['pending', 'confirmed']
        ).order_by('scheduled_date')
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'consultations': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get consultation history for the user"""
        queryset = self.get_queryset().filter(
            status__in=['completed', 'cancelled', 'no_show']
        ).order_by('-scheduled_date')
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        paginated_queryset = queryset[start:end]
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        return Response({
            'success': True,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'consultations': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get consultation statistics for the current user"""
        user = request.user
        
        # Check if user is a consultant
        is_consultant = ConsultantProfile.objects.filter(user=user, is_active=True).exists()
        
        if is_consultant:
            # Consultant stats
            bookings = ConsultationBooking.objects.filter(
                consultant=user,
                booking_type='physical'
            )
            
            return Response({
                'success': True,
                'role': 'consultant',
                'stats': {
                    'total_consultations': bookings.count(),
                    'completed': bookings.filter(status='completed').count(),
                    'pending': bookings.filter(status='pending').count(),
                    'confirmed': bookings.filter(status='confirmed').count(),
                    'cancelled': bookings.filter(status='cancelled').count(),
                    'total_earnings': float(bookings.filter(
                        status='completed'
                    ).aggregate(Sum('consultant_earnings'))['consultant_earnings__sum'] or 0),
                    'upcoming_count': bookings.filter(
                        scheduled_date__gte=timezone.now(),
                        status__in=['pending', 'confirmed']
                    ).count()
                }
            })
        else:
            # Client stats
            bookings = ConsultationBooking.objects.filter(
                client=user,
                booking_type='physical'
            )
            
            return Response({
                'success': True,
                'role': 'client',
                'stats': {
                    'total_consultations': bookings.count(),
                    'completed': bookings.filter(status='completed').count(),
                    'pending': bookings.filter(status='pending').count(),
                    'confirmed': bookings.filter(status='confirmed').count(),
                    'cancelled': bookings.filter(status='cancelled').count(),
                    'total_spent': float(bookings.filter(
                        status='completed'
                    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                    'upcoming_count': bookings.filter(
                        scheduled_date__gte=timezone.now(),
                        status__in=['pending', 'confirmed']
                    ).count()
                }
            })
