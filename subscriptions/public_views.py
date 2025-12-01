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
    ConsultantReview,
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
    
    @action(detail=False, methods=['post'], url_path='apply')
    def apply_to_consult(self, request):
        """
        Apply to become a consultant (advocates, lawyers, paralegals)
        
        Simplified process - most data is already collected during registration:
        - consultant_type: Comes from user.user_role.role_name
        - Documents: Already uploaded during verification
        - Personal info: Already in user profile
        
        Requirements:
        - User must be verified (advocate, lawyer, or paralegal)
        - Must accept terms and conditions
        - Physical consultations require law firm association
        """
        # Check if user has a role
        if not request.user.user_role:
            return Response({
                'error': 'User role not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is eligible
        eligible_types = ['advocate', 'lawyer', 'paralegal']
        if request.user.user_role.role_name not in eligible_types:
            return Response({
                'error': 'Only verified advocates, lawyers, and paralegals can apply to become consultants'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user is verified
        if not request.user.is_verified:
            return Response({
                'error': 'Your account must be verified before applying to become a consultant'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user already has a pending or approved application
        existing = ConsultantRegistrationRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'approved']
        ).first()
        
        if existing:
            return Response({
                'error': f'You already have a {existing.status} consultant application',
                'application': ConsultantRegistrationRequestSerializer(existing, context={'request': request}).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already has a consultant profile
        if hasattr(request.user, 'consultant_profile'):
            return Response({
                'error': 'You are already a registered consultant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ConsultantRegistrationCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Get validated data
            validated_data = serializer.validated_data.copy()
            validated_data.pop('terms_accepted')  # Remove write-only field
            
            # Use user's role_name as consultant_type
            consultant_type = request.user.user_role.role_name
            
            # Create registration request with data from user profile
            # Get city from law firm or user's address
            city = ''
            if request.user.associated_law_firm:
                city = getattr(request.user.associated_law_firm, 'city', '')
            elif hasattr(request.user, 'address') and request.user.address:
                city = getattr(request.user.address.district, 'name', '') if request.user.address.district else ''
            
            registration = ConsultantRegistrationRequest.objects.create(
                user=request.user,
                consultant_type=consultant_type,
                # Consultation preferences from request
                offers_physical_consultations=validated_data.get('offers_physical_consultations', False),
                # Mobile consultations always offered by default
                offers_mobile_consultations=True,
                # Use law firm city, user district, or empty string
                preferred_consultation_city=city,
            )
            
            return Response({
                'success': True,
                'message': 'Consultant application submitted successfully',
                'registration': ConsultantRegistrationRequestSerializer(registration, context={'request': request}).data,
                'next_steps': [
                    'Your application will be reviewed by our admin team',
                    'You will be notified via email once reviewed',
                    'If approved, you can start accepting consultation requests'
                ]
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='application-status', permission_classes=[IsAuthenticated])
    def check_application_status(self, request):
        """
        Check current consultant application status
        Requires authentication
        """
        # Check if user has a consultant profile
        if hasattr(request.user, 'consultant_profile'):
            profile = request.user.consultant_profile
            return Response({
                'is_consultant': True,
                'status': 'approved',
                'profile_id': profile.id,
                'consultant_type': profile.consultant_type,
                'is_available': profile.is_available
            })
        
        # Check for pending/rejected applications
        application = ConsultantRegistrationRequest.objects.filter(
            user=request.user
        ).order_by('-created_at').first()
        
        if application:
            return Response({
                'is_consultant': False,
                'status': application.status,
                'application': ConsultantRegistrationRequestSerializer(application, context={'request': request}).data
            })
        
        # Check if user is eligible
        eligible_types = ['advocate', 'lawyer', 'paralegal', 'law_firm']
        can_apply = (request.user.user_role and 
                    request.user.user_role.role_name in eligible_types and 
                    request.user.is_verified)
        
        return Response({
            'is_consultant': False,
            'status': 'not_applied',
            'can_apply': can_apply,
            'message': 'No consultant application found' if can_apply else 'You are not eligible to apply as a consultant'
        })
    
    @action(detail=False, methods=['get', 'patch'], url_path='my-profile')
    def my_consultant_profile(self, request):
        """
        Get or update current user's consultant profile with comprehensive statistics
        
        GET: Returns consultant profile with:
            - User details (name, email, phone, profile picture, bio)
            - Consultation statistics (total, by type, by status)
            - Earnings breakdown (total, pending, paid out, by type)
            - Performance metrics (ratings, reviews)
            - Service offerings and availability
        
        PATCH: Update consultant profile fields and user information
        Updatable fields:
        - User fields: bio, profile_picture, first_name, last_name, phone_number
        - Profile fields: specialization, years_of_experience, city, is_available
        - Service offerings: offers_mobile_consultations, offers_physical_consultations
        """
        try:
            profile = ConsultantProfile.objects.get(user=request.user)
            
            if request.method == 'GET':
                # Get consultation statistics
                from django.db.models import Count, Sum, Q, Avg
                from datetime import datetime, timedelta
                
                consultations = ConsultationBooking.objects.filter(consultant=request.user)
                
                # Consultation stats by type and status
                consultation_stats = {
                    'total': consultations.count(),
                    'by_type': {
                        'mobile': consultations.filter(booking_type='mobile').count(),
                        'physical': consultations.filter(booking_type='physical').count(),
                    },
                    'by_status': {
                        'completed': consultations.filter(status='completed').count(),
                        'in_progress': consultations.filter(status='in_progress').count(),
                        'confirmed': consultations.filter(status='confirmed').count(),
                        'pending': consultations.filter(status='pending').count(),
                        'cancelled': consultations.filter(status='cancelled').count(),
                    },
                    'this_month': consultations.filter(
                        created_at__gte=datetime.now().replace(day=1)
                    ).count(),
                    'this_week': consultations.filter(
                        created_at__gte=datetime.now() - timedelta(days=7)
                    ).count(),
                }
                
                # Earnings statistics
                earnings_records = ConsultantEarnings.objects.filter(consultant=request.user)
                
                earnings_stats = {
                    'total_gross': float(earnings_records.aggregate(
                        total=Sum('gross_amount')
                    )['total'] or 0),
                    'total_net': float(earnings_records.aggregate(
                        total=Sum('net_earnings')
                    )['total'] or 0),
                    'pending': float(earnings_records.filter(paid_out=False).aggregate(
                        total=Sum('net_earnings')
                    )['total'] or 0),
                    'paid_out': float(earnings_records.filter(paid_out=True).aggregate(
                        total=Sum('net_earnings')
                    )['total'] or 0),
                    'by_type': {
                        'mobile': float(earnings_records.filter(
                            service_type__icontains='MOBILE'
                        ).aggregate(total=Sum('net_earnings'))['total'] or 0),
                        'physical': float(earnings_records.filter(
                            service_type__icontains='PHYSICAL'
                        ).aggregate(total=Sum('net_earnings'))['total'] or 0),
                    },
                    'this_month': float(earnings_records.filter(
                        created_at__gte=datetime.now().replace(day=1)
                    ).aggregate(total=Sum('net_earnings'))['total'] or 0),
                    'count': earnings_records.count(),
                }
                
                # Performance metrics with reviews
                reviews = ConsultantReview.objects.filter(consultant=request.user, is_visible=True)
                
                performance = {
                    'average_rating': float(profile.average_rating),
                    'total_reviews': profile.total_reviews,
                    'completion_rate': round(
                        (consultation_stats['by_status']['completed'] / consultation_stats['total'] * 100) 
                        if consultation_stats['total'] > 0 else 0, 
                        2
                    ),
                    'rating_breakdown': {
                        '5_stars': reviews.filter(rating=5).count(),
                        '4_stars': reviews.filter(rating=4).count(),
                        '3_stars': reviews.filter(rating=3).count(),
                        '2_stars': reviews.filter(rating=2).count(),
                        '1_star': reviews.filter(rating=1).count(),
                    },
                    'average_professionalism': float(reviews.exclude(
                        professionalism_rating__isnull=True
                    ).aggregate(avg=Avg('professionalism_rating'))['avg'] or 0),
                    'average_communication': float(reviews.exclude(
                        communication_rating__isnull=True
                    ).aggregate(avg=Avg('communication_rating'))['avg'] or 0),
                    'average_expertise': float(reviews.exclude(
                        expertise_rating__isnull=True
                    ).aggregate(avg=Avg('expertise_rating'))['avg'] or 0),
                }
                
                # Add recent reviews (last 5)
                recent_reviews = reviews.order_by('-created_at')[:5].values(
                    'id', 'rating', 'review_text', 'created_at',
                    'professionalism_rating', 'communication_rating', 'expertise_rating',
                    'consultant_response', 'response_date'
                )
                
                performance['recent_reviews'] = list(recent_reviews)
                
                # Serialize profile data
                serializer = ConsultantProfileSerializer(profile, context={'request': request})
                profile_data = serializer.data
                
                # Add comprehensive statistics
                profile_data['statistics'] = {
                    'consultations': consultation_stats,
                    'earnings': earnings_stats,
                    'performance': performance,
                }
                
                return Response(profile_data)
            
            elif request.method == 'PATCH':
                # Update consultant profile fields
                profile_fields = [
                    'specialization', 'years_of_experience',
                    'offers_mobile_consultations', 'offers_physical_consultations',
                    'city', 'is_available'
                ]
                
                updated_fields = []
                
                # Update ConsultantProfile fields
                for field in profile_fields:
                    if field in request.data:
                        setattr(profile, field, request.data[field])
                        updated_fields.append(field)
                
                if updated_fields:
                    profile.save()
                
                # Update user profile fields (bio, profile_picture, name, phone)
                user_fields = ['bio', 'profile_picture', 'first_name', 'last_name', 'phone_number']
                user_updated = []
                
                for field in user_fields:
                    if field in request.data or field in request.FILES:
                        value = request.FILES.get(field) if field == 'profile_picture' else request.data.get(field)
                        if value is not None:
                            setattr(request.user, field, value)
                            user_updated.append(field)
                
                if user_updated:
                    request.user.save()
                
                # Return updated profile with stats
                serializer = ConsultantProfileSerializer(profile, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'updated_fields': {
                        'profile': updated_fields,
                        'user': user_updated
                    },
                    'profile': serializer.data
                })
        
        except ConsultantProfile.DoesNotExist:
            return Response(
                {'error': 'You do not have an active consultant profile'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='my-reviews')
    def my_consultant_reviews(self, request):
        """
        Get all reviews for the authenticated consultant
        
        Query params:
        - page: Page number for pagination
        - page_size: Number of reviews per page (default 10)
        - rating: Filter by specific rating (1-5)
        - responded: Filter by whether consultant has responded (true/false)
        """
        try:
            profile = ConsultantProfile.objects.get(user=request.user)
        except ConsultantProfile.DoesNotExist:
            return Response(
                {'error': 'You do not have a consultant profile'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reviews = ConsultantReview.objects.filter(
            consultant=request.user,
            is_visible=True
        ).select_related('client', 'booking')
        
        # Apply filters
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            reviews = reviews.filter(rating=int(rating_filter))
        
        responded_filter = request.query_params.get('responded')
        if responded_filter:
            if responded_filter.lower() == 'true':
                reviews = reviews.exclude(consultant_response='')
            elif responded_filter.lower() == 'false':
                reviews = reviews.filter(consultant_response='')
        
        # Prepare response data
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'client': {
                    'name': review.client.get_full_name(),
                    'email': review.client.email if request.user.is_staff else None,
                },
                'booking_id': review.booking.id,
                'booking_type': review.booking.booking_type,
                'booking_date': review.booking.scheduled_date,
                'rating': review.rating,
                'review_text': review.review_text,
                'professionalism_rating': review.professionalism_rating,
                'communication_rating': review.communication_rating,
                'expertise_rating': review.expertise_rating,
                'consultant_response': review.consultant_response,
                'response_date': review.response_date,
                'created_at': review.created_at,
            })
        
        return Response({
            'count': len(reviews_data),
            'reviews': reviews_data,
            'summary': {
                'average_rating': float(profile.average_rating),
                'total_reviews': profile.total_reviews,
            }
        })
    
    @action(detail=True, methods=['post'], url_path='respond-to-review')
    def respond_to_review(self, request, pk=None):
        """
        Consultant responds to a review
        
        Body:
        - response: Response text
        """
        try:
            review = ConsultantReview.objects.get(
                id=pk,
                consultant=request.user
            )
        except ConsultantReview.DoesNotExist:
            return Response(
                {'error': 'Review not found or you do not have permission'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        response_text = request.data.get('response', '').strip()
        if not response_text:
            return Response(
                {'error': 'Response text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.consultant_response = response_text
        review.response_date = timezone.now()
        review.save()
        
        return Response({
            'success': True,
            'message': 'Response submitted successfully',
            'review': {
                'id': review.id,
                'response': review.consultant_response,
                'response_date': review.response_date,
            }
        })


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
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ConsultationBooking.objects.none()
        
        user = self.request.user
        
        # Check if user is a consultant
        try:
            consultant_profile = ConsultantProfile.objects.get(user=user)
            # Return bookings where user is either client or consultant
            return ConsultationBooking.objects.filter(
                Q(client=user) | Q(consultant_profile=consultant_profile)
            ).select_related(
                'client', 'consultant_profile__user', 'payment_transaction', 'call_session'
            ).order_by('-created_at')
        except ConsultantProfile.DoesNotExist:
            # User is not a consultant, return only their client bookings
            return ConsultationBooking.objects.filter(
                client=user
            ).select_related(
                'consultant_profile__user', 'payment_transaction', 'call_session'
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
        """
        Submit a review for a completed consultation
        
        Body:
        - rating: Overall rating (1-5 stars) [required]
        - review_text: Written review [optional]
        - professionalism_rating: Professionalism rating (1-5) [optional]
        - communication_rating: Communication rating (1-5) [optional]
        - expertise_rating: Legal expertise rating (1-5) [optional]
        """
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
        
        # Check if already reviewed
        if hasattr(booking, 'review'):
            return Response(
                {'error': 'You have already reviewed this consultation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate rating
        rating = request.data.get('rating')
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
        
        # Get optional ratings
        review_text = request.data.get('review_text', '').strip()
        professionalism_rating = request.data.get('professionalism_rating')
        communication_rating = request.data.get('communication_rating')
        expertise_rating = request.data.get('expertise_rating')
        
        # Validate optional ratings
        for field_name, field_value in [
            ('professionalism_rating', professionalism_rating),
            ('communication_rating', communication_rating),
            ('expertise_rating', expertise_rating)
        ]:
            if field_value is not None:
                try:
                    field_value = int(field_value)
                    if field_value < 1 or field_value > 5:
                        raise ValueError
                except (ValueError, TypeError):
                    return Response(
                        {'error': f'{field_name} must be an integer between 1 and 5'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        # Create review
        review = ConsultantReview.objects.create(
            consultant=booking.consultant,
            client=booking.client,
            booking=booking,
            rating=rating,
            review_text=review_text,
            professionalism_rating=int(professionalism_rating) if professionalism_rating else None,
            communication_rating=int(communication_rating) if communication_rating else None,
            expertise_rating=int(expertise_rating) if expertise_rating else None,
        )
        
        # Update consultant's profile statistics
        consultant_profile = booking.consultant.consultant_profile
        reviews = ConsultantReview.objects.filter(consultant=booking.consultant, is_visible=True)
        
        consultant_profile.average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        consultant_profile.total_reviews = reviews.count()
        consultant_profile.save()
        
        return Response({
            'success': True,
            'message': 'Review submitted successfully',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'review_text': review.review_text,
                'professionalism_rating': review.professionalism_rating,
                'communication_rating': review.communication_rating,
                'expertise_rating': review.expertise_rating,
                'created_at': review.created_at,
            },
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
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return PaymentTransaction.objects.none()
        
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
    queryset = ConsultantEarnings.objects.none()  # Placeholder for schema
    serializer_class = ConsultantEarningsSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ConsultantEarnings.objects.none()
        return ConsultantEarnings.objects.filter(consultant=self.request.user)
    
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
