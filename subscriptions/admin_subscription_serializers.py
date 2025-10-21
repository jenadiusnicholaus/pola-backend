"""
Admin Subscription Management Serializers
Handles subscription plans and user subscriptions management
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscription, PaymentTransaction
from authentication.models import PolaUser


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Admin serializer for subscription plans"""
    total_subscribers = serializers.SerializerMethodField()
    active_subscribers = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    benefits_en = serializers.SerializerMethodField()
    benefits_sw = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'plan_type', 'name', 'name_sw', 'description', 'description_sw',
            'price', 'currency', 'duration_days', 'is_active',
            'full_legal_library_access', 'monthly_questions_limit',
            'free_documents_per_month', 'legal_updates', 'forum_access',
            'student_hub_access', 'benefits_en', 'benefits_sw',
            'total_subscribers', 'active_subscribers',
            'total_revenue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        ref_name = 'AdminSubscriptionPlan'
    
    def get_total_subscribers(self, obj):
        """Get total number of subscribers"""
        return obj.subscriptions.count()
    
    def get_active_subscribers(self, obj):
        """Get count of active subscribers"""
        return obj.subscriptions.filter(status='active', end_date__gt=timezone.now()).count()
    
    def get_total_revenue(self, obj):
        """Calculate total revenue from this plan (excludes free trials)"""
        # Free trial plans should never generate revenue
        if obj.plan_type == 'free_trial' or obj.price == 0:
            return 0.0
        
        completed_transactions = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            related_subscription__plan=obj,
            status='completed'
        ).exclude(amount=0)  # Exclude free trial transactions with 0 amount
        total = sum(t.amount for t in completed_transactions)
        return float(total)
    
    def get_benefits_en(self, obj):
        """Get benefits in English"""
        return obj.get_benefits_dict(language='en')
    
    def get_benefits_sw(self, obj):
        """Get benefits in Swahili"""
        return obj.get_benefits_dict(language='sw')


class UserSubscriptionAdminSerializer(serializers.ModelSerializer):
    """Admin serializer for user subscriptions"""
    user_details = serializers.SerializerMethodField()
    plan_details = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()
    payment_history = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'user_details', 'plan', 'plan_details', 'status',
            'start_date', 'end_date', 'auto_renew', 'device_id',
            'questions_asked_this_month', 'documents_generated_this_month',
            'last_reset_date', 'usage_stats', 'payment_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        ref_name = 'AdminUserSubscription'
    
    def get_user_details(self, obj):
        """Get user information"""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'full_name': f"{obj.user.first_name} {obj.user.last_name}",
            'phone': getattr(obj.user, 'phone_number', None)
        }
    
    def get_plan_details(self, obj):
        """Get plan information"""
        return {
            'id': obj.plan.id,
            'name': obj.plan.name,
            'type': obj.plan.plan_type,
            'price': float(obj.plan.price),
            'currency': obj.plan.currency
        }
    
    def get_usage_stats(self, obj):
        """Get usage statistics"""
        return {
            'questions_used': obj.questions_asked_this_month,
            'questions_limit': obj.plan.monthly_questions_limit,
            'documents_generated': obj.documents_generated_this_month,
            'documents_limit': obj.plan.free_documents_per_month,
            'days_remaining': obj.days_remaining(),
            'is_active': obj.is_active()
        }
    
    def get_payment_history(self, obj):
        """Get payment transaction history"""
        transactions = PaymentTransaction.objects.filter(
            user=obj.user,
            transaction_type='subscription',
            related_subscription=obj
        ).order_by('-created_at')[:5]
        
        return [{
            'id': t.id,
            'amount': float(t.amount),
            'status': t.status,
            'payment_method': t.payment_method,
            'created_at': t.created_at
        } for t in transactions]


class ExtendSubscriptionSerializer(serializers.Serializer):
    """Serializer for extending subscription"""
    days = serializers.IntegerField(min_value=1, max_value=365)
    reason = serializers.CharField(required=False, allow_blank=True)


class GrantSubscriptionSerializer(serializers.Serializer):
    """Serializer for granting free subscription"""
    user_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()
    duration_days = serializers.IntegerField(min_value=1, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            PolaUser.objects.get(id=value)
        except PolaUser.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value
    
    def validate_plan_id(self, value):
        """Validate plan exists"""
        try:
            SubscriptionPlan.objects.get(id=value)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Plan not found")
        return value


class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics"""
    total_plans = serializers.IntegerField()
    active_plans = serializers.IntegerField()
    total_subscribers = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()
    expired_subscribers = serializers.IntegerField()
    trial_users = serializers.IntegerField()
    paid_users = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    churn_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
