"""
Public Views - Phase 3: Public-Facing API Endpoints

These ViewSets expose the public-facing APIs for:
- Consultant registration and profiles
- Consultation booking (mobile & physical)
- Call credit purchase and management
- Payment transactions
- Pricing information

Uses serializers from: subscriptions/public_serializers.py
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Q, Sum, Avg
from decimal import Decimal
import uuid

from .models import (
    PricingConfiguration,
    CallCreditBundle,
    ConsultantProfile,
    ConsultantRegistrationRequest,
    ConsultationBooking,
    CallSession,
    PaymentTransaction,
    ConsultantEarnings,
    UploaderEarnings,
)
from .public_serializers import (
    PricingConfigurationSerializer,
    CallCreditBundleSerializer,
    ConsultantProfileSerializer,
    ConsultantRegistrationRequestSerializer,
    ConsultantRegistrationCreateSerializer,
    ConsultationBookingSerializer,
    ConsultationBookingCreateSerializer,
    CallSessionSerializer,
    PaymentTransactionSerializer,
    PaymentInitiationSerializer,
    ConsultantEarningsSerializer,
    UploaderEarningsSerializer,
)
from .azampay_integration import (
    azampay_client,
    detect_mobile_provider,
    format_phone_number,
)


# ==============================================================================
# PRICING & CONFIGURATION
# ==============================================================================

class PricingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for pricing configuration
    
    Endpoints:
    - GET /api/v1/pricing/ - List all active pricing
    - GET /api/v1/pricing/{id}/ - Get specific pricing
    - GET /api/v1/pricing/by-service/?type=mobile_consultation - Get pricing by service type
    """
    queryset = PricingConfiguration.objects.filter(is_active=True)
    serializer_class = PricingConfigurationSerializer
    permission_classes = [AllowAny]  # Public pricing information
    
    @action(detail=False, methods=['get'])
    def by_service(self, request):
        """Get pricing for a specific service type"""
        service_type = request.query_params.get('type')
        if not service_type:
            return Response(
                {'error': 'Service type is required. Use ?type=mobile_consultation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pricing = PricingConfiguration.objects.get(
                service_type=service_type,
                is_active=True
            )
            serializer = self.get_serializer(pricing)
            return Response(serializer.data)
        except PricingConfiguration.DoesNotExist:
            return Response(
                {'error': f'Pricing not found for service type: {service_type}'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==============================================================================
# CALL CREDITS (VOUCHERS)
# ==============================================================================

class CallCreditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for call credit bundles
    
    Endpoints:
    - GET /api/v1/call-credits/bundles/ - List all available bundles
    - GET /api/v1/call-credits/bundles/{id}/ - Get specific bundle
    - POST /api/v1/call-credits/purchase/ - Purchase a bundle
    - GET /api/v1/call-credits/my-balance/ - Get current user's balance
    """
    queryset = CallCreditBundle.objects.filter(is_active=True)
    serializer_class = CallCreditBundleSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='bundles')
    def list_bundles(self, request):
        """List all available call credit bundles"""
        bundles = self.get_queryset().order_by('price')
        serializer = self.get_serializer(bundles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """Purchase a call credit bundle"""
        bundle_id = request.data.get('bundle_id')
        payment_method = request.data.get('payment_method', 'mobile_money')
        phone_number = request.data.get('phone_number')
        
        if not bundle_id:
            return Response(
                {'error': 'bundle_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bundle = CallCreditBundle.objects.get(id=bundle_id, is_active=True)
        except CallCreditBundle.DoesNotExist:
            return Response(
                {'error': 'Bundle not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate payment method
        if payment_method == 'mobile_money' and not phone_number:
            return Response(
                {'error': 'phone_number is required for mobile money payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment transaction and voucher
        with db_transaction.atomic():
            from .models import ConsultationVoucher
            from datetime import timedelta
            
            # Create voucher (initially marked as used, will be activated on payment success)
            voucher = ConsultationVoucher.objects.create(
                user=request.user,
                voucher_type='call_credit',
                duration_minutes=bundle.minutes,
                purchased_date=timezone.now(),
                expiry_date=timezone.now() + timedelta(days=bundle.validity_days),
                is_used=True,  # Mark as used until payment confirms
                voucher_code=f"CC-{uuid.uuid4().hex[:8].upper()}"
            )
            
            # Create payment transaction
            transaction = PaymentTransaction.objects.create(
                user=request.user,
                transaction_type='call_credit',
                amount=bundle.price,
                currency=bundle.currency,
                payment_method=payment_method,
                payment_reference=f"CC-{uuid.uuid4().hex[:12].upper()}",
                description=f"Purchase {bundle.minutes} minutes call credit bundle",
                status='pending',
                related_voucher=voucher
            )
            
            # Initiate AzamPay payment
            if payment_method == 'mobile_money':
                formatted_phone = format_phone_number(phone_number)
                provider = detect_mobile_provider(formatted_phone)
                
                # Check if AzamPay is configured
                if not azampay_client.config.is_configured():
                    return Response({
                        'message': 'Payment initiated (TEST MODE - AzamPay not configured)',
                        'transaction': PaymentTransactionSerializer(transaction).data,
                        'payment_details': {
                            'transaction_id': transaction.id,
                            'payment_reference': transaction.payment_reference,
                            'amount': float(bundle.price),
                            'currency': bundle.currency,
                            'bundle': {
                                'minutes': bundle.minutes,
                                'type': bundle.bundle_type,
                                'validity_days': bundle.validity_days
                            },
                            'phone': formatted_phone,
                            'provider': provider
                        },
                        'test_mode': True,
                        'next_step': 'Configure AzamPay credentials in settings to enable real payments'
                    }, status=status.HTTP_201_CREATED)
                
                # Initiate real payment
                payment_result = azampay_client.initiate_checkout(
                    phone_number=formatted_phone,
                    amount=bundle.price,
                    external_reference=transaction.payment_reference,
                    provider=provider
                )
                
                if payment_result['success']:
                    # Update transaction with AzamPay reference
                    transaction.gateway_reference = payment_result['transaction_id']
                    transaction.save()
                    
                    return Response({
                        'message': 'Payment initiated successfully',
                        'transaction': PaymentTransactionSerializer(transaction).data,
                        'payment_details': {
                            'transaction_id': transaction.id,
                            'payment_reference': transaction.payment_reference,
                            'azampay_transaction_id': payment_result['transaction_id'],
                            'amount': float(bundle.price),
                            'currency': bundle.currency,
                            'bundle': {
                                'minutes': bundle.minutes,
                                'type': bundle.bundle_type,
                                'validity_days': bundle.validity_days
                            },
                            'phone': formatted_phone,
                            'provider': provider
                        },
                        'next_step': f'Please complete payment on your {provider} phone: {formatted_phone}'
                    }, status=status.HTTP_201_CREATED)
                else:
                    # Payment initiation failed
                    transaction.status = 'failed'
                    transaction.save()
                    
                    return Response({
                        'error': 'Payment initiation failed',
                        'message': payment_result['message']
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # For non-mobile-money payments (future: card, bank)
            return Response({
                'message': 'Payment method not yet supported',
                'transaction': PaymentTransactionSerializer(transaction).data,
                'supported_methods': ['mobile_money']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-balance')
    def my_balance(self, request):
        """Get current user's call credit balance"""
        from .models import ConsultationVoucher
        
        # Get active vouchers
        active_vouchers = ConsultationVoucher.objects.filter(
            user=request.user,
            is_used=False,
            expiry_date__gt=timezone.now()
        )
        
        total_minutes = sum(v.duration_minutes for v in active_vouchers)
        
        return Response({
            'total_minutes': total_minutes,
            'active_vouchers': active_vouchers.count(),
            'vouchers': [
                {
                    'id': v.id,
                    'minutes': v.duration_minutes,
                    'voucher_code': v.voucher_code,
                    'expires_at': v.expiry_date,
                    'purchased_at': v.purchased_date
                }
                for v in active_vouchers
            ]
        })


# ==============================================================================
# CONSULTANT PROFILES
# ==============================================================================

class ConsultantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for consultant profiles
    
    Endpoints:
    - GET /api/v1/consultants/ - List all verified consultants
    - GET /api/v1/consultants/{id}/ - Get consultant details
    - POST /api/v1/consultants/register/ - Apply to become a consultant
    - GET /api/v1/consultants/my-profile/ - Get current user's consultant profile
    - GET /api/v1/consultants/search/ - Search consultants by specialization
    """
    # Only show consultants who have been approved (have a profile)
    queryset = ConsultantProfile.objects.filter(is_available=True)
    serializer_class = ConsultantProfileSerializer
    permission_classes = [AllowAny]  # Public can browse consultants
    
    def get_permissions(self):
        """Override permissions for specific actions"""
        if self.action in ['register', 'my_profile']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search consultants by various criteria"""
        specialization = request.query_params.get('specialization')
        consultant_type = request.query_params.get('type')
        min_rating = request.query_params.get('min_rating')
        
        queryset = self.get_queryset()
        
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        
        if consultant_type:
            queryset = queryset.filter(consultant_type=consultant_type)
        
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass
        
        # Order by rating and experience
        queryset = queryset.order_by('-rating', '-years_of_experience')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Apply to become a consultant"""
        serializer = ConsultantRegistrationCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if user already has a pending or approved application
            existing = ConsultantRegistrationRequest.objects.filter(
                applicant=request.user,
                status__in=['pending', 'approved']
            ).exists()
            
            if existing:
                return Response(
                    {'error': 'You already have a pending or approved consultant application'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create registration request
            registration = ConsultantRegistrationRequest.objects.create(
                applicant=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'message': 'Consultant registration submitted successfully',
                'registration': ConsultantRegistrationRequestSerializer(registration).data,
                'next_step': 'Your application will be reviewed by our admin team'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        """Get current user's consultant profile"""
        try:
            profile = ConsultantProfile.objects.get(consultant=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except ConsultantProfile.DoesNotExist:
            # Check if user has a pending application
            pending = ConsultantRegistrationRequest.objects.filter(
                applicant=request.user,
                status='pending'
            ).exists()
            
            if pending:
                return Response(
                    {'message': 'Your consultant application is pending review'},
                    status=status.HTTP_200_OK
                )
            
            return Response(
                {'error': 'You are not registered as a consultant'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==============================================================================
# CONSULTATION BOOKINGS
# ==============================================================================

class ConsultationBookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for consultation bookings
    
    Endpoints:
    - POST /api/v1/consultations/book/ - Book a consultation
    - GET /api/v1/consultations/ - List user's bookings
    - GET /api/v1/consultations/{id}/ - Get booking details
    - PATCH /api/v1/consultations/{id}/cancel/ - Cancel a booking
    - POST /api/v1/consultations/{id}/start-call/ - Start a call session
    - POST /api/v1/consultations/{id}/end-call/ - End a call session
    - POST /api/v1/consultations/{id}/rate/ - Rate a consultation
    """
    serializer_class = ConsultationBookingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return bookings for current user (as client or consultant)"""
        user = self.request.user
        
        # Check if user is a consultant
        try:
            consultant_profile = ConsultantProfile.objects.get(consultant=user)
            # Return bookings where user is either client or consultant
            return ConsultationBooking.objects.filter(
                Q(client=user) | Q(consultant_profile=consultant_profile)
            ).select_related(
                'client', 'consultant_profile__consultant', 'payment_transaction', 'call_session'
            ).order_by('-created_at')
        except ConsultantProfile.DoesNotExist:
            # User is not a consultant, return only their client bookings
            return ConsultationBooking.objects.filter(
                client=user
            ).select_related(
                'consultant_profile__consultant', 'payment_transaction', 'call_session'
            ).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def book(self, request):
        """Create a new consultation booking"""
        serializer = ConsultationBookingCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            consultant_profile_id = serializer.validated_data['consultant_profile_id']
            
            try:
                consultant_profile = ConsultantProfile.objects.get(id=consultant_profile_id)
            except ConsultantProfile.DoesNotExist:
                return Response(
                    {'error': 'Consultant not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get pricing
            pricing = consultant_profile.get_pricing()
            consultation_type = serializer.validated_data['consultation_type']
            service_key = 'mobile' if consultation_type == 'mobile' else 'physical'
            amount = pricing[service_key]['price']
            
            # Create booking
            with db_transaction.atomic():
                booking = ConsultationBooking.objects.create(
                    client=request.user,
                    consultant_profile=consultant_profile,
                    consultation_type=consultation_type,
                    topic=serializer.validated_data['topic'],
                    description=serializer.validated_data['description'],
                    scheduled_date=serializer.validated_data.get('scheduled_date'),
                    scheduled_time=serializer.validated_data.get('scheduled_time'),
                    duration_minutes=serializer.validated_data.get('duration_minutes', 30),
                    location=serializer.validated_data.get('location', ''),
                    status='pending_payment',
                    amount_paid=amount
                )
                
                # Create payment transaction
                payment = PaymentTransaction.objects.create(
                    user=request.user,
                    transaction_type='consultation',
                    amount=amount,
                    currency='TZS',
                    payment_method=serializer.validated_data.get('payment_method', 'mobile_money'),
                    payment_reference=f"CONS-{uuid.uuid4().hex[:12].upper()}",
                    description=f"Consultation booking: {booking.topic}",
                    status='pending',
                    related_booking=booking
                )
                
                booking.payment_transaction = payment
                booking.save()
                
                # For physical consultations, initiate payment
                phone_number = request.data.get('phone_number')
                
                if consultation_type == 'physical' and amount > 0:
                    if not phone_number:
                        return Response({
                            'error': 'phone_number is required for physical consultation payments'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check if AzamPay is configured
                    if azampay_client.config.is_configured():
                        formatted_phone = format_phone_number(phone_number)
                        provider = detect_mobile_provider(formatted_phone)
                        
                        # Initiate payment
                        payment_result = azampay_client.initiate_checkout(
                            phone_number=formatted_phone,
                            amount=amount,
                            external_reference=payment.payment_reference,
                            provider=provider
                        )
                        
                        if payment_result['success']:
                            payment.gateway_reference = payment_result['transaction_id']
                            payment.save()
                            
                            return Response({
                                'message': 'Consultation booking created and payment initiated',
                                'booking': ConsultationBookingSerializer(booking).data,
                                'payment': PaymentTransactionSerializer(payment).data,
                                'payment_details': {
                                    'azampay_transaction_id': payment_result['transaction_id'],
                                    'phone': formatted_phone,
                                    'provider': provider
                                },
                                'next_step': f'Complete payment on your {provider} phone: {formatted_phone}'
                            }, status=status.HTTP_201_CREATED)
                        else:
                            return Response({
                                'error': 'Payment initiation failed',
                                'message': payment_result['message'],
                                'booking': ConsultationBookingSerializer(booking).data
                            }, status=status.HTTP_400_BAD_REQUEST)
                
                # For mobile consultations (FREE) or test mode
                return Response({
                    'message': 'Consultation booking created successfully',
                    'booking': ConsultationBookingSerializer(booking).data,
                    'payment': PaymentTransactionSerializer(payment).data,
                    'next_step': 'Complete payment to confirm booking' if amount > 0 else 'Booking confirmed (FREE mobile consultation)'
                }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        # Check if user is the client
        if booking.client != request.user:
            return Response(
                {'error': 'You can only cancel your own bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking can be cancelled
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel a {booking.status} booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        # TODO: Handle refund if payment was completed
        
        return Response({
            'message': 'Booking cancelled successfully',
            'booking': self.get_serializer(booking).data
        })
    
    @action(detail=True, methods=['post'], url_path='start-call')
    def start_call(self, request, pk=None):
        """Start a call session for mobile consultation"""
        booking = self.get_object()
        
        # Validate booking
        if booking.consultation_type != 'mobile':
            return Response(
                {'error': 'Call sessions are only for mobile consultations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.status != 'confirmed':
            return Response(
                {'error': 'Booking must be confirmed to start a call'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.call_session:
            return Response(
                {'error': 'Call session already exists for this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create call session
        call_session = CallSession.objects.create(
            booking=booking,
            status='active',
            started_at=timezone.now()
        )
        
        booking.call_session = call_session
        booking.status = 'in_progress'
        booking.save()
        
        return Response({
            'message': 'Call session started',
            'session': CallSessionSerializer(call_session).data
        })
    
    @action(detail=True, methods=['post'], url_path='end-call')
    def end_call(self, request, pk=None):
        """End a call session"""
        booking = self.get_object()
        
        if not booking.call_session:
            return Response(
                {'error': 'No active call session found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        call_session = booking.call_session
        
        if call_session.status != 'active':
            return Response(
                {'error': 'Call session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # End call session
        call_session.ended_at = timezone.now()
        call_session.status = 'completed'
        
        # Calculate duration and credits used
        duration = (call_session.ended_at - call_session.started_at).total_seconds() / 60
        call_session.actual_duration_minutes = int(duration)
        call_session.credits_used = Decimal(str(duration))
        call_session.save()
        
        booking.status = 'completed'
        booking.save()
        
        # Create consultant earnings
        pricing = booking.consultant_profile.get_pricing()
        ConsultantEarnings.objects.create(
            consultant=booking.consultant_profile.consultant,
            booking=booking,
            service_type='mobile_consultation',
            gross_amount=booking.amount_paid or 0,
            platform_commission=(booking.amount_paid or 0) * Decimal(str(pricing['mobile']['split']['platform'])) / 100,
            net_earnings=(booking.amount_paid or 0) * Decimal(str(pricing['mobile']['split']['consultant'])) / 100
        )
        
        return Response({
            'message': 'Call session ended',
            'session': CallSessionSerializer(call_session).data,
            'booking': self.get_serializer(booking).data
        })
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a completed consultation"""
        booking = self.get_object()
        
        # Check if user is the client
        if booking.client != request.user:
            return Response(
                {'error': 'You can only rate your own bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if booking is completed
        if booking.status != 'completed':
            return Response(
                {'error': 'You can only rate completed consultations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
        if not rating:
            return Response(
                {'error': 'Rating is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'Rating must be an integer between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.client_rating = rating
        booking.client_feedback = feedback
        booking.save()
        
        # Update consultant's average rating
        consultant_profile = booking.consultant_profile
        avg_rating = ConsultationBooking.objects.filter(
            consultant_profile=consultant_profile,
            client_rating__isnull=False
        ).aggregate(avg=Avg('client_rating'))['avg']
        
        consultant_profile.rating = avg_rating or 0
        consultant_profile.save()
        
        return Response({
            'message': 'Rating submitted successfully',
            'booking': self.get_serializer(booking).data
        })


# ==============================================================================
# PAYMENT TRANSACTIONS
# ==============================================================================

class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for payment transactions
    
    Endpoints:
    - GET /api/v1/payments/ - List user's transactions
    - GET /api/v1/payments/{id}/ - Get transaction details
    - POST /api/v1/payments/initiate/ - Initiate a payment
    - GET /api/v1/payments/{id}/status/ - Check payment status
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return transactions for current user"""
        return PaymentTransaction.objects.filter(
            user=self.request.user
        ).select_related(
            'related_booking__consultant_profile',
            'related_subscription__plan',
            'related_voucher'
        ).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a new payment"""
        serializer = PaymentInitiationSerializer(data=request.data)
        
        if serializer.is_valid():
            # TODO: Integrate with AzamPay here
            
            return Response({
                'message': 'Payment initiation endpoint - AzamPay integration pending',
                'data': serializer.validated_data,
                'note': 'This will be implemented in Phase 4'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Check payment status"""
        transaction = self.get_object()
        
        # Check status with AzamPay if pending and has gateway reference
        if transaction.status == 'pending' and transaction.gateway_reference:
            if azampay_client.config.is_configured():
                status_result = azampay_client.check_payment_status(
                    payment_reference=transaction.payment_reference,
                    azampay_transaction_id=transaction.gateway_reference
                )
                
                if status_result['success']:
                    azampay_status = status_result['status']
                    
                    # Update transaction based on AzamPay status
                    if azampay_status == 'SUCCESS' and transaction.status != 'completed':
                        # Process payment success (similar to webhook)
                        with db_transaction.atomic():
                            transaction.status = 'completed'
                            transaction.save()
                            
                            # Handle related items
                            if transaction.related_booking:
                                transaction.related_booking.status = 'confirmed'
                                transaction.related_booking.save()
                            
                            if transaction.related_voucher:
                                transaction.related_voucher.is_used = False
                                transaction.related_voucher.save()
                    
                    elif azampay_status == 'FAILED':
                        transaction.status = 'failed'
                        transaction.save()
                
                return Response({
                    'transaction_id': transaction.id,
                    'payment_reference': transaction.payment_reference,
                    'azampay_transaction_id': transaction.gateway_reference,
                    'status': transaction.status,
                    'azampay_status': status_result.get('status', 'UNKNOWN'),
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'created_at': transaction.created_at,
                    'updated_at': transaction.updated_at,
                    'last_checked': timezone.now()
                })
        
        # Return current status
        return Response({
            'transaction_id': transaction.id,
            'payment_reference': transaction.payment_reference,
            'status': transaction.status,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'created_at': transaction.created_at,
            'updated_at': transaction.updated_at
        })


# ==============================================================================
# EARNINGS
# ==============================================================================

class EarningsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for consultant/uploader earnings
    
    Endpoints:
    - GET /api/v1/earnings/consultant/ - Get consultant earnings
    - GET /api/v1/earnings/uploader/ - Get uploader earnings
    - GET /api/v1/earnings/summary/ - Get earnings summary
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def consultant(self, request):
        """Get consultant earnings"""
        earnings = ConsultantEarnings.objects.filter(
            consultant=request.user
        ).select_related('booking').order_by('-created_at')
        
        serializer = ConsultantEarningsSerializer(earnings, many=True)
        
        # Calculate summary
        total_gross = sum(e.gross_amount for e in earnings)
        total_commission = sum(e.platform_commission for e in earnings)
        total_net = sum(e.net_earnings for e in earnings)
        paid_out = sum(e.net_earnings for e in earnings if e.paid_out)
        pending = total_net - paid_out
        
        return Response({
            'earnings': serializer.data,
            'summary': {
                'total_gross': float(total_gross),
                'total_commission': float(total_commission),
                'total_net': float(total_net),
                'paid_out': float(paid_out),
                'pending': float(pending),
                'count': earnings.count()
            }
        })
    
    @action(detail=False, methods=['get'])
    def uploader(self, request):
        """Get uploader earnings"""
        earnings = UploaderEarnings.objects.filter(
            uploader=request.user
        ).select_related('material').order_by('-created_at')
        
        serializer = UploaderEarningsSerializer(earnings, many=True)
        
        # Calculate summary
        total_gross = sum(e.gross_amount for e in earnings)
        total_commission = sum(e.platform_commission for e in earnings)
        total_net = sum(e.net_earnings for e in earnings)
        paid_out = sum(e.net_earnings for e in earnings if e.paid_out)
        pending = total_net - paid_out
        
        return Response({
            'earnings': serializer.data,
            'summary': {
                'total_gross': float(total_gross),
                'total_commission': float(total_commission),
                'total_net': float(total_net),
                'paid_out': float(paid_out),
                'pending': float(pending),
                'count': earnings.count()
            }
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get combined earnings summary"""
        # Consultant earnings
        consultant_earnings = ConsultantEarnings.objects.filter(consultant=request.user)
        consultant_total = sum(e.net_earnings for e in consultant_earnings)
        consultant_pending = sum(e.net_earnings for e in consultant_earnings if not e.paid_out)
        
        # Uploader earnings
        uploader_earnings = UploaderEarnings.objects.filter(uploader=request.user)
        uploader_total = sum(e.net_earnings for e in uploader_earnings)
        uploader_pending = sum(e.net_earnings for e in uploader_earnings if not e.paid_out)
        
        return Response({
            'consultant': {
                'total': float(consultant_total),
                'pending': float(consultant_pending),
                'count': consultant_earnings.count()
            },
            'uploader': {
                'total': float(uploader_total),
                'pending': float(uploader_pending),
                'count': uploader_earnings.count()
            },
            'combined': {
                'total': float(consultant_total + uploader_total),
                'pending': float(consultant_pending + uploader_pending),
                'total_count': consultant_earnings.count() + uploader_earnings.count()
            }
        })
