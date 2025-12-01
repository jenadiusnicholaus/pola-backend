"""
Phase 2 Serializers - Public API Support
Created: October 15, 2025

These serializers enable the public-facing API endpoints for:
- Consultant registration and profiles
- Consultation booking (mobile & physical)
- Call credit (voucher) purchase and management
- Payment transactions (AzamPay integration)
- Earnings tracking

All serializers follow best practices:
- Proper validation
- Read-only fields
- Nested serializers for related data
- Custom methods for complex logic
"""

from rest_framework import serializers
from django.utils import timezone
from django.db import transaction as db_transaction
from decimal import Decimal
from datetime import timedelta

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
    DocumentType,
)
from documents.models import LearningMaterial
from authentication.models import PolaUser


# ==============================================================================
# PRICING & CALL CREDIT SERIALIZERS
# ==============================================================================

class PricingConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for pricing configuration"""
    revenue_split = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = PricingConfiguration
        fields = [
            'id', 'service_type', 'price',
            'platform_commission_percent', 'consultant_share_percent',
            'revenue_split', 'formatted_price', 'is_active',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_revenue_split(self, obj):
        """Return readable revenue split"""
        return {
            'platform': f"{obj.platform_commission_percent}%",
            'consultant': f"{obj.consultant_share_percent}%",
            'platform_amount': float(obj.price * obj.platform_commission_percent / 100),
            'consultant_amount': float(obj.price * obj.consultant_share_percent / 100),
        }
    
    def get_formatted_price(self, obj):
        """Return formatted price string"""
        if obj.price == 0:
            return {
                'amount': 0,
                'display': 'FREE',
                'currency': 'TZS',
                'note': 'Requires call credits for mobile consultations'
            }
        return {
            'amount': float(obj.price),
            'display': f"{float(obj.price):,.0f} TZS",
            'currency': 'TZS'
        }


class CallCreditBundleSerializer(serializers.ModelSerializer):
    """Serializer for call credit bundles"""
    formatted_price = serializers.SerializerMethodField()
    per_minute_cost = serializers.SerializerMethodField()
    savings = serializers.SerializerMethodField()
    
    class Meta:
        model = CallCreditBundle
        fields = [
            'id', 'name', 'name_sw', 'description', 'description_sw', 'minutes', 'price',
            'validity_days', 'formatted_price', 'per_minute_cost',
            'savings', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_formatted_price(self, obj):
        return f"{float(obj.price):,.0f} TZS"
    
    def get_per_minute_cost(self, obj):
        """Calculate cost per minute"""
        cost_per_minute = obj.price / obj.minutes
        return {
            'amount': float(cost_per_minute),
            'formatted': f"{float(cost_per_minute):,.0f} TZS/min"
        }
    
    def get_savings(self, obj):
        """Calculate savings compared to standard rate (if any)"""
        # Assume standard rate is 1000 TZS/min (you can adjust)
        standard_rate = 1000
        bundle_rate = obj.price / obj.minutes
        if bundle_rate < standard_rate:
            savings_percent = ((standard_rate - bundle_rate) / standard_rate) * 100
            total_savings = (standard_rate - bundle_rate) * obj.minutes
            return {
                'percent': round(savings_percent, 1),
                'amount': float(total_savings),
                'formatted': f"Save {savings_percent:.0f}%"
            }
        return None


# ==============================================================================
# CONSULTANT SERIALIZERS
# ==============================================================================

class ConsultantProfileSerializer(serializers.ModelSerializer):
    """Serializer for consultant profiles"""
    user_details = serializers.SerializerMethodField()
    pricing_info = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultantProfile
        fields = [
            'id', 'user', 'user_details', 'consultant_type',
            'specialization', 'years_of_experience',
            'offers_mobile_consultations', 'offers_physical_consultations',
            'city', 'is_available', 'total_consultations',
            'total_earnings', 'average_rating', 'total_reviews',
            'verification_status', 'pricing_info', 'statistics',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'total_consultations', 'total_earnings',
            'average_rating', 'total_reviews', 'created_at', 'updated_at'
        ]
    
    def get_user_details(self, obj):
        """Get consultant user details"""
        user = obj.user
        request = self.context.get('request')
        
        # Build profile picture URL
        profile_picture_url = None
        if user.profile_picture:
            if request:
                profile_picture_url = request.build_absolute_uri(user.profile_picture.url)
            else:
                profile_picture_url = user.profile_picture.url
        
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}",
            'phone_number': user.phone_number if hasattr(user, 'phone_number') else None,
            'bio': user.bio if hasattr(user, 'bio') else None,
            'profile_picture': profile_picture_url,
        }
    
    def get_pricing_info(self, obj):
        """Get pricing information for this consultant"""
        pricing = obj.get_pricing()
        result = {}
        
        if 'mobile' in pricing:
            result['mobile'] = {
                'price': float(pricing['mobile']['price']),
                'formatted': f"{float(pricing['mobile']['price']):,.0f} TZS" if pricing['mobile']['price'] > 0 else "FREE",
                'requires_credits': pricing['mobile']['price'] == 0,
                'revenue_split': {
                    'consultant': f"{pricing['mobile']['consultant_share']}%",
                    'platform': f"{pricing['mobile']['platform_share']}%"
                },
                'note': 'Requires call credits' if pricing['mobile']['price'] == 0 else None
            }
        
        if 'physical' in pricing:
            result['physical'] = {
                'price': float(pricing['physical']['price']),
                'formatted': f"{float(pricing['physical']['price']):,.0f} TZS",
                'revenue_split': {
                    'consultant': f"{pricing['physical']['consultant_share']}%",
                    'platform': f"{pricing['physical']['platform_share']}%"
                }
            }
        
        return result
    
    def get_statistics(self, obj):
        """Get consultant statistics"""
        return {
            'total_consultations': obj.total_consultations,
            'average_rating': float(obj.average_rating) if obj.average_rating else 0,
            'total_reviews': obj.total_reviews,
            'years_experience': obj.years_of_experience,
            'specialization': obj.specialization,
        }
    
    def get_verification_status(self, obj):
        """Get verification status details"""
        # A consultant is verified if they have an approved profile
        has_registration = bool(obj.registration_request)
        return {
            'is_verified': has_registration,  # Having a profile means they're approved
            'has_registration': has_registration,
            'verification_level': 'verified' if has_registration else 'active'
        }


class ConsultantRegistrationRequestSerializer(serializers.ModelSerializer):
    """Serializer for consultant registration requests"""
    user_details = serializers.SerializerMethodField()
    professional_info = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    consultant_type_display = serializers.CharField(source='get_consultant_type_display', read_only=True)
    
    class Meta:
        model = ConsultantRegistrationRequest
        ref_name = 'PublicConsultantRegistrationRequest'
        fields = [
            'id', 'user', 'user_details', 'consultant_type', 'consultant_type_display',
            'license_document', 'id_document', 'cv_document', 'additional_documents',
            'offers_mobile_consultations', 'offers_physical_consultations',
            'preferred_consultation_city', 'professional_info',
            'status', 'status_display', 'admin_notes',
            'reviewed_by', 'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'status', 'admin_notes', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at'
        ]
    
    def get_user_details(self, obj):
        """Get user details"""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'full_name': obj.user.get_full_name(),
            'phone': obj.user.contact.phone_number if hasattr(obj.user, 'contact') else None,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }
    
    def get_professional_info(self, obj):
        """Get professional information from user profile"""
        return obj.get_professional_info()


class ConsultantRegistrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating consultant registration requests"""
    terms_accepted = serializers.BooleanField(write_only=True, required=True)
    
    class Meta:
        model = ConsultantRegistrationRequest
        fields = [
            'consultant_type', 'license_document', 'id_document',
            'cv_document', 'additional_documents',
            'offers_mobile_consultations', 'offers_physical_consultations',
            'preferred_consultation_city', 'terms_accepted'
        ]
    
    def validate_terms_accepted(self, value):
        """Ensure terms are accepted"""
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions")
        return value
    
    def validate_id_document(self, value):
        """Validate ID document is provided"""
        if not value:
            raise serializers.ValidationError("ID document is required")
        return value
    
    def validate_consultant_type(self, value):
        """Validate consultant type matches user's role"""
        user = self.context['request'].user
        
        if not user.user_role:
            raise serializers.ValidationError("User role not found")
        
        # Map user roles to consultant types
        type_mapping = {
            'advocate': ['advocate'],
            'lawyer': ['lawyer'],
            'paralegal': ['paralegal'],
            'law_firm': ['advocate', 'lawyer']  # Law firms can register as advocate or lawyer
        }
        
        allowed_types = type_mapping.get(user.user_role.role_name, [])
        
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Your role ({user.user_role.role_name}) cannot register as {value}"
            )
        
        return value
    
    def validate(self, attrs):
        """Validate physical consultations eligibility"""
        user = self.context['request'].user
        
        if not user.user_role:
            raise serializers.ValidationError("User role not found")
        
        # Only law firms can offer physical consultations
        if attrs.get('offers_physical_consultations', False) and user.user_role.role_name != 'law_firm':
            raise serializers.ValidationError({
                'offers_physical_consultations': 'Only registered law firms can offer physical consultations'
            })
        
        # If offering physical consultations, city is required
        if attrs.get('offers_physical_consultations') and not attrs.get('preferred_consultation_city'):
            raise serializers.ValidationError({
                'preferred_consultation_city': 'City is required for physical consultations'
            })
        
        return attrs


class ConsultantRegistrationCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating consultant registration requests.
    Most information (consultant_type, documents, personal info) is already collected
    during user registration and verification, so we only need consultation preferences.
    """
    offers_physical_consultations = serializers.BooleanField(default=False)
    terms_accepted = serializers.BooleanField(required=True, write_only=True)
    
    def validate_terms_accepted(self, value):
        """Ensure terms are accepted"""
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions")
        return value
    
    def validate(self, data):
        """
        Validate based on user's role and firm association.
        Physical consultations require advocate/lawyer role AND law firm association.
        """
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        user = request.user
        
        # Check if user has a role
        if not user.user_role:
            raise serializers.ValidationError("User role not found")
        
        # Physical consultations validation
        if data.get('offers_physical_consultations'):
            # Must be advocate or lawyer
            if user.user_role.role_name not in ['advocate', 'lawyer']:
                raise serializers.ValidationError({
                    'offers_physical_consultations': 
                    'Only advocates and lawyers can offer physical consultations'
                })
            
            # Must be associated with a law firm
            if not user.associated_law_firm:
                raise serializers.ValidationError({
                    'offers_physical_consultations': 
                    'You must be associated with a law firm to offer physical consultations'
                })
        
        return data


# ==============================================================================
# CONSULTATION BOOKING SERIALIZERS
# ==============================================================================

class ConsultationBookingSerializer(serializers.ModelSerializer):
    """Serializer for consultation bookings"""
    client_details = serializers.SerializerMethodField()
    consultant_details = ConsultantProfileSerializer(source='consultant.consultant_profile', read_only=True)
    call_session_details = serializers.SerializerMethodField()
    pricing_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultationBooking
        fields = [
            'id', 'client', 'client_details', 'consultant',
            'consultant_details', 'booking_type', 'status',
            'scheduled_date', 'scheduled_duration_minutes',
            'actual_start_time', 'actual_end_time', 'actual_duration_minutes',
            'total_amount', 'platform_commission', 'consultant_earnings',
            'meeting_location', 'client_notes', 'consultant_notes',
            'call_session_details', 'pricing_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'client', 'status', 'actual_start_time', 'actual_end_time',
            'actual_duration_minutes', 'created_at', 'updated_at'
        ]
    
    def get_client_details(self, obj):
        """Get client user details"""
        user = obj.client
        return {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}",
        }
    
    def get_call_session_details(self, obj):
        """Get call session details if exists"""
        # ConsultationBooking doesn't have call_session field in current model
        # This would need to be implemented if call sessions are tracked separately
        return None
    
    def get_pricing_details(self, obj):
        """Get pricing breakdown"""
        return {
            'booking_type': obj.booking_type,
            'total_amount': float(obj.total_amount),
            'platform_commission': float(obj.platform_commission),
            'consultant_earnings': float(obj.consultant_earnings),
            'currency': 'TZS'
        }


class ConsultationBookingCreateSerializer(serializers.Serializer):
    """Serializer for creating consultation bookings"""
    consultant_profile_id = serializers.IntegerField(required=True)
    consultation_type = serializers.ChoiceField(
        choices=['mobile', 'physical'],
        required=True
    )
    topic = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(min_value=5, required=False, default=30)
    location = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(
        choices=['mobile_money', 'card', 'bank_transfer'],
        default='mobile_money'
    )
    
    def validate_consultant_profile_id(self, value):
        """Validate consultant profile exists"""
        try:
            profile = ConsultantProfile.objects.get(id=value)
            if not profile.is_available:
                raise serializers.ValidationError("This consultant is not currently available")
            # Consultants with profiles are already verified (approved by admin)
        except ConsultantProfile.DoesNotExist:
            raise serializers.ValidationError("Consultant profile not found")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Physical consultations require date, time, and location
        if data.get('consultation_type') == 'physical':
            if not data.get('scheduled_date'):
                raise serializers.ValidationError({
                    'scheduled_date': 'Scheduled date is required for physical consultations'
                })
            if not data.get('scheduled_time'):
                raise serializers.ValidationError({
                    'scheduled_time': 'Scheduled time is required for physical consultations'
                })
            if not data.get('location'):
                raise serializers.ValidationError({
                    'location': 'Location is required for physical consultations'
                })
        
        return data


class CallSessionSerializer(serializers.ModelSerializer):
    """Serializer for call sessions"""
    booking_details = serializers.SerializerMethodField()
    duration_info = serializers.SerializerMethodField()
    
    class Meta:
        model = CallSession
        fields = [
            'id', 'booking', 'booking_details', 'call_credit',
            'start_time', 'end_time', 'duration_minutes',
            'call_quality_rating', 'duration_info', 'created_at'
        ]
        read_only_fields = [
            'booking', 'call_credit', 'duration_minutes', 'created_at'
        ]
    
    def get_booking_details(self, obj):
        """Get basic booking info"""
        return {
            'id': obj.booking.id,
            'booking_type': obj.booking.booking_type,
            'client': f"{obj.booking.client.first_name} {obj.booking.client.last_name}",
        }
    
    def get_duration_info(self, obj):
        """Get duration information"""
        if obj.start_time and not obj.end_time:
            elapsed = (timezone.now() - obj.start_time).total_seconds() / 60
            return {
                'status': 'active',
                'elapsed_minutes': round(elapsed, 2),
                'started_at': obj.start_time,
            }
        elif obj.end_time:
            return {
                'status': 'completed',
                'total_minutes': obj.duration_minutes,
                'started_at': obj.start_time,
                'ended_at': obj.end_time,
            }
        return {'status': 'pending', 'started_at': obj.start_time}


# ==============================================================================
# PAYMENT TRANSACTION SERIALIZERS
# ==============================================================================

class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for payment transactions"""
    user_details = serializers.SerializerMethodField()
    transaction_details = serializers.SerializerMethodField()
    related_items = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'user', 'user_details', 'transaction_type',
            'amount', 'currency', 'payment_method', 'payment_reference',
            'gateway_reference', 'status', 'description',
            'transaction_details', 'related_items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'payment_reference', 'gateway_reference',
            'created_at', 'updated_at'
        ]
    
    def get_user_details(self, obj):
        """Get user details"""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}",
        }
    
    def get_transaction_details(self, obj):
        """Get formatted transaction details"""
        return {
            'type': obj.get_transaction_type_display(),
            'amount': float(obj.amount),
            'currency': obj.currency,
            'formatted_amount': f"{float(obj.amount):,.0f} {obj.currency}",
            'payment_method': obj.get_payment_method_display(),
            'status': obj.get_status_display(),
            'reference': obj.payment_reference,
        }
    
    def get_related_items(self, obj):
        """Get related items (booking, subscription, etc.)"""
        related = {}
        
        if obj.related_booking:
            related['booking'] = {
                'id': obj.related_booking.id,
                'booking_type': obj.related_booking.booking_type,
                'client': f"{obj.related_booking.client.first_name} {obj.related_booking.client.last_name}",
            }
        
        if obj.related_subscription:
            related['subscription'] = {
                'id': obj.related_subscription.id,
                'plan': obj.related_subscription.plan.name,
            }
        
        return related if related else None


class PaymentInitiationSerializer(serializers.Serializer):
    """Serializer for initiating payments"""
    transaction_type = serializers.ChoiceField(
        choices=['subscription', 'consultation', 'document', 'material', 'call_credit'],
        required=True
    )
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    payment_method = serializers.ChoiceField(
        choices=['mobile_money', 'card', 'bank_transfer'],
        default='mobile_money'
    )
    phone_number = serializers.CharField(max_length=15, required=False)
    item_id = serializers.IntegerField(required=True, help_text="ID of the item being purchased")
    
    def validate_phone_number(self, value):
        """Validate phone number for mobile money"""
        if self.initial_data.get('payment_method') == 'mobile_money':
            if not value:
                raise serializers.ValidationError("Phone number is required for mobile money payments")
            # Add phone number format validation here
        return value


# ==============================================================================
# EARNINGS SERIALIZERS  
# ==============================================================================

class ConsultantEarningsSerializer(serializers.ModelSerializer):
    """Serializer for consultant earnings"""
    consultant_details = serializers.SerializerMethodField()
    booking_details = serializers.SerializerMethodField()
    earning_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultantEarnings
        ref_name = 'PublicConsultantEarnings'
        fields = [
            'id', 'consultant', 'consultant_details', 'booking',
            'booking_details', 'service_type', 'gross_amount',
            'platform_commission', 'net_earnings', 'earning_details',
            'paid_out', 'payout_date', 'created_at'
        ]
        read_only_fields = [
            'consultant', 'booking', 'gross_amount', 'platform_commission',
            'net_earnings', 'created_at'
        ]
    
    def get_consultant_details(self, obj):
        """Get consultant details"""
        user = obj.consultant
        return {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}",
        }
    
    def get_booking_details(self, obj):
        """Get booking details if exists"""
        if not obj.booking:
            return None
        return {
            'id': obj.booking.id,
            'booking_type': obj.booking.booking_type,
            'date': obj.booking.scheduled_date,
        }
    
    def get_earning_details(self, obj):
        """Get formatted earning details"""
        return {
            'gross': float(obj.gross_amount),
            'commission': float(obj.platform_commission),
            'net': float(obj.net_earnings),
            'formatted_net': f"{float(obj.net_earnings):,.0f} TZS",
            'paid': obj.paid_out,
            'payout_date': obj.payout_date,
        }


class UploaderEarningsSerializer(serializers.ModelSerializer):
    """Serializer for uploader earnings"""
    uploader_details = serializers.SerializerMethodField()
    material_details = serializers.SerializerMethodField()
    earning_details = serializers.SerializerMethodField()
    
    class Meta:
        model = UploaderEarnings
        fields = [
            'id', 'uploader', 'uploader_details', 'material',
            'material_details', 'service_type', 'gross_amount',
            'platform_commission', 'net_earnings', 'earning_details',
            'paid_out', 'payout_date', 'created_at'
        ]
        read_only_fields = [
            'uploader', 'material', 'gross_amount', 'platform_commission',
            'net_earnings', 'created_at'
        ]
    
    def get_uploader_details(self, obj):
        """Get uploader details"""
        user = obj.uploader
        return {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}",
        }
    
    def get_material_details(self, obj):
        """Get material details if exists"""
        if not obj.material:
            return None
        return {
            'id': obj.material.id,
            'title': obj.material.title,
            'category': obj.material.category,
        }
    
    def get_earning_details(self, obj):
        """Get formatted earning details"""
        return {
            'gross': float(obj.gross_amount),
            'commission': float(obj.platform_commission),
            'net': float(obj.net_earnings),
            'formatted_net': f"{float(obj.net_earnings):,.0f} TZS",
            'paid': obj.paid_out,
            'payout_date': obj.payout_date,
        }
