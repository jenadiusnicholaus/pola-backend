"""
Admin Consultation Management Serializers
Handles pricing configurations, consultant profiles, and physical bookings
"""

from rest_framework import serializers
from .models import (
    PricingConfiguration, ConsultantProfile, ConsultationBooking,
    ConsultantEarnings, PaymentTransaction
)
from authentication.models import PolaUser
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal


class ConsultantUserSerializer(serializers.ModelSerializer):
    """Nested serializer for consultant user details"""
    phone_number = serializers.SerializerMethodField()
    
    class Meta:
        model = PolaUser
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'is_active']
        ref_name = 'AdminConsultantUser'
    
    def get_phone_number(self, obj):
        """Get phone number from related Contact model"""
        try:
            return obj.contact.phone_number
        except:
            return None


class PricingConfigurationAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for pricing configuration"""
    total_bookings = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = PricingConfiguration
        fields = [
            'id', 'service_type', 'price', 'platform_commission_percent',
            'consultant_share_percent', 'description', 'is_active',
            'created_at', 'updated_at',
            'total_bookings', 'total_revenue'
        ]
        ref_name = 'AdminPricingConfiguration'
    
    def get_total_bookings(self, obj):
        """Count bookings using this pricing - only for consultation types"""
        if 'MOBILE' in obj.service_type or 'PHYSICAL' in obj.service_type:
            booking_type = 'mobile' if 'MOBILE' in obj.service_type else 'physical'
            return ConsultationBooking.objects.filter(booking_type=booking_type).count()
        return 0
    
    def get_total_revenue(self, obj):
        """Calculate revenue - only for consultation types"""
        if 'MOBILE' in obj.service_type or 'PHYSICAL' in obj.service_type:
            booking_type = 'mobile' if 'MOBILE' in obj.service_type else 'physical'
            bookings = ConsultationBooking.objects.filter(
                booking_type=booking_type,
                status='completed'
            )
            return sum(b.total_amount for b in bookings)
        return Decimal('0')


class ConsultantProfileAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for consultant profiles"""
    user = ConsultantUserSerializer(read_only=True)
    total_bookings = serializers.SerializerMethodField()
    completed_bookings = serializers.SerializerMethodField()
    cancelled_bookings = serializers.SerializerMethodField()
    pending_bookings = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultantProfile
        fields = [
            'id', 'user', 'consultant_type', 'specialization', 'years_of_experience',
            'offers_mobile_consultations', 'offers_physical_consultations', 'city',
            'is_available', 'total_consultations', 'total_earnings', 
            'average_rating', 'total_reviews', 'created_at', 'updated_at',
            'total_bookings', 'completed_bookings', 'cancelled_bookings', 'pending_bookings'
        ]
        ref_name = 'AdminConsultantProfile'
    
    def get_total_bookings(self, obj):
        """Count all bookings"""
        return ConsultationBooking.objects.filter(consultant=obj.user).count()
    
    def get_completed_bookings(self, obj):
        """Count completed bookings"""
        return ConsultationBooking.objects.filter(
            consultant=obj.user, status='completed'
        ).count()
    
    def get_cancelled_bookings(self, obj):
        """Count cancelled bookings"""
        return ConsultationBooking.objects.filter(
            consultant=obj.user, status='cancelled'
        ).count()
    
    def get_pending_bookings(self, obj):
        """Count pending bookings"""
        return ConsultationBooking.objects.filter(
            consultant=obj.user, status='pending'
        ).count()
    
    def to_representation(self, instance):
        """Ensure numeric fields are JSON-compliant"""
        data = super().to_representation(instance)
        
        # Handle average_rating to prevent infinity
        if 'average_rating' in data:
            try:
                rating = float(data['average_rating'])
                # Check for infinity or NaN
                if rating == float('inf') or rating == float('-inf') or rating != rating:
                    data['average_rating'] = 0.0
                else:
                    # Clamp to valid range
                    data['average_rating'] = max(0.0, min(5.0, rating))
            except (ValueError, TypeError):
                data['average_rating'] = 0.0
        
        # Handle total_earnings to prevent infinity
        if 'total_earnings' in data:
            try:
                earnings = float(data['total_earnings'])
                if earnings == float('inf') or earnings == float('-inf') or earnings != earnings:
                    data['total_earnings'] = 0.0
            except (ValueError, TypeError):
                data['total_earnings'] = 0.0
        
        return data


class ConsultationBookingAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for consultation bookings"""
    client = ConsultantUserSerializer(read_only=True)
    consultant = ConsultantUserSerializer(read_only=True)
    consultant_profile_details = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultationBooking
        fields = [
            'id', 'client', 'consultant', 'consultant_profile_details',
            'booking_type', 'status', 'scheduled_date', 'scheduled_duration_minutes',
            'actual_start_time', 'actual_end_time', 'actual_duration_minutes',
            'total_amount', 'platform_commission', 'consultant_earnings',
            'meeting_location', 'client_notes', 'consultant_notes',
            'created_at', 'updated_at', 'payment_details'
        ]
        ref_name = 'AdminConsultationBooking'
    
    def get_consultant_profile_details(self, obj):
        """Get consultant profile details"""
        try:
            profile = obj.consultant.consultant_profile
            # Ensure average_rating is a valid number
            avg_rating = profile.average_rating
            if avg_rating is None:
                avg_rating = Decimal('0')
            # Clamp to valid range
            avg_rating = max(Decimal('0'), min(Decimal('5'), avg_rating))
            
            return {
                'id': profile.id,
                'consultant_type': profile.consultant_type,
                'specialization': profile.specialization,
                'years_of_experience': profile.years_of_experience,
                'is_available': profile.is_available,
                'average_rating': float(avg_rating)
            }
        except (ConsultantProfile.DoesNotExist, AttributeError):
            return None
    
    def get_payment_details(self, obj):
        """Get payment transaction details"""
        payment = PaymentTransaction.objects.filter(
            transaction_type='physical_consultation',
            user=obj.client
        ).order_by('-created_at').first()
        
        if not payment:
            return None
        
        return {
            'id': payment.id,
            'amount': payment.amount,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'transaction_id': payment.payment_reference,
            'timestamp': payment.created_at
        }


class UpdateBookingStatusSerializer(serializers.Serializer):
    """Serializer for updating booking status"""
    status = serializers.ChoiceField(
        choices=['pending', 'confirmed', 'completed', 'cancelled'],
        required=True
    )
    admin_note = serializers.CharField(required=False, allow_blank=True)


class ConsultationStatsSerializer(serializers.Serializer):
    """Serializer for consultation statistics"""
    # Pricing configs
    total_pricing_configs = serializers.IntegerField()
    
    # Consultants
    total_consultants = serializers.IntegerField()
    active_consultants = serializers.IntegerField()
    
    # Bookings
    total_bookings = serializers.IntegerField()
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    completed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    
    # Revenue
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_platform_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_consultant_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Hours
    total_consultation_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_consultation_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Ratings
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
