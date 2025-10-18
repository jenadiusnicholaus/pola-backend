"""
Admin Call Credit Bundle Management Serializers
Handles call credit bundles (consultation vouchers) management
"""

from rest_framework import serializers
from django.utils import timezone
from .models import CallCreditBundle, UserCallCredit, CallSession, PaymentTransaction
from authentication.models import PolaUser


class CallCreditBundleAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for call credit bundles"""
    total_purchases = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    total_minutes_sold = serializers.SerializerMethodField()
    total_minutes_used = serializers.SerializerMethodField()
    
    class Meta:
        model = CallCreditBundle
        fields = [
            'id', 'name', 'name_sw', 'description', 'description_sw', 'minutes', 'price', 
            'validity_days', 'is_active', 'total_purchases', 'total_revenue', 
            'total_minutes_sold', 'total_minutes_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        ref_name = 'AdminCallCreditBundle'
    
    def get_total_purchases(self, obj):
        """Get total number of purchases"""
        return UserCallCredit.objects.filter(bundle=obj).count()
    
    def get_total_revenue(self, obj):
        """Calculate total revenue from this bundle"""
        completed_transactions = PaymentTransaction.objects.filter(
            transaction_type='call_credit',
            description__contains=f"Bundle #{obj.id}",
            status='completed'
        )
        total = sum(t.amount for t in completed_transactions)
        return float(total)
    
    def get_total_minutes_sold(self, obj):
        """Total minutes sold"""
        credits = UserCallCredit.objects.filter(bundle=obj)
        return sum(c.total_minutes for c in credits)
    
    def get_total_minutes_used(self, obj):
        """Total minutes actually used"""
        credits = UserCallCredit.objects.filter(bundle=obj)
        return sum(c.total_minutes - c.remaining_minutes for c in credits)


class UserCallCreditAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for user call credits"""
    user_details = serializers.SerializerMethodField()
    bundle_details = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = UserCallCredit
        fields = [
            'id', 'user', 'user_details', 'bundle', 'bundle_details',
            'total_minutes', 'remaining_minutes', 'purchase_date',
            'expiry_date', 'status', 'usage_stats'
        ]
        ref_name = 'AdminUserCallCredit'
    
    def get_user_details(self, obj):
        """Get user information"""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}"
        }
    
    def get_bundle_details(self, obj):
        """Get bundle information"""
        return {
            'id': obj.bundle.id,
            'name': obj.bundle.name,
            'price': float(obj.bundle.price)
        }
    
    def get_usage_stats(self, obj):
        """Get usage statistics"""
        used_minutes = obj.total_minutes - obj.remaining_minutes
        usage_percent = (used_minutes / obj.total_minutes * 100) if obj.total_minutes > 0 else 0
        
        return {
            'used_minutes': used_minutes,
            'usage_percent': round(usage_percent, 2),
            'is_valid': obj.is_valid(),
            'days_until_expiry': (obj.expiry_date - timezone.now()).days if obj.expiry_date > timezone.now() else 0
        }


class GrantCallCreditSerializer(serializers.Serializer):
    """Serializer for granting free call credits"""
    user_id = serializers.IntegerField()
    minutes = serializers.IntegerField(min_value=1)
    validity_days = serializers.IntegerField(min_value=1, default=30)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            PolaUser.objects.get(id=value)
        except PolaUser.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value


class CallCreditStatsSerializer(serializers.Serializer):
    """Serializer for call credit statistics"""
    total_bundles = serializers.IntegerField()
    active_bundles = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_minutes_sold = serializers.IntegerField()
    total_minutes_used = serializers.IntegerField()
    total_minutes_remaining = serializers.IntegerField()
    active_credits = serializers.IntegerField()
    expired_credits = serializers.IntegerField()
    average_usage_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
