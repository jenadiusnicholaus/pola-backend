"""
Serializers for Subscription Management API
Handles subscription data serialization and validation
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from subscriptions.models import UserSubscription


class SubscriptionAdminListSerializer(serializers.ModelSerializer):
    """Serializer for subscription list view"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'user_email', 'user_name', 'plan', 'plan_name',
            'start_date', 'end_date', 'status', 'auto_renew', 'amount',
            'currency', 'days_remaining', 'is_active', 'created_at', 'updated_at'
        ]
    
    def get_days_remaining(self, obj):
        if obj.end_date:
            delta = obj.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def get_is_active(self, obj):
        return obj.status == 'active' and obj.end_date and obj.end_date > timezone.now()


class SubscriptionAdminDetailSerializer(SubscriptionAdminListSerializer):
    """Detailed serializer for subscription view"""
    renewal_count = serializers.IntegerField(read_only=True)
    last_renewal_date = serializers.DateTimeField(read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta(SubscriptionAdminListSerializer.Meta):
        fields = SubscriptionAdminListSerializer.Meta.fields + [
            'renewal_count', 'last_renewal_date', 'payment_method_display', 'status_display'
        ]


class SubscriptionAdminCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating subscriptions"""
    
    class Meta:
        model = UserSubscription
        fields = [
            'user', 'plan', 'start_date', 'end_date', 'status', 
            'auto_renew', 'payment_method', 'amount', 'currency'
        ]
    
    def validate(self, data):
        # Validate dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise serializers.ValidationError(
                    "End date must be after start date"
                )
        
        # Validate status
        status = data.get('status')
        if status not in ['active', 'expired', 'cancelled', 'suspended']:
            raise serializers.ValidationError(
                "Invalid status. Must be: active, expired, cancelled, or suspended"
            )
        
        return data


class SubscriptionTimeExtensionSerializer(serializers.Serializer):
    """Serializer for extending subscription time"""
    extend_days = serializers.IntegerField(min_value=0, max_value=365)
    extend_hours = serializers.IntegerField(min_value=0, max_value=23, required=False, default=0)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notify_user = serializers.BooleanField(required=False, default=False)
    
    def validate_extend_days(self, value):
        if value == 0:
            raise serializers.ValidationError(
                "Extend days must be greater than 0"
            )
        return value


class SubscriptionEndDateSerializer(serializers.Serializer):
    """Serializer for setting custom end date"""
    end_date = serializers.DateTimeField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notify_user = serializers.BooleanField(required=False, default=False)
    
    def validate_end_date(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "End date must be in the future"
            )
        return value


class SubscriptionPeriodResetSerializer(serializers.Serializer):
    """Serializer for resetting subscription period"""
    new_start_date = serializers.DateTimeField()
    new_end_date = serializers.DateTimeField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    reset_renewal_count = serializers.BooleanField(required=False, default=False)
    notify_user = serializers.BooleanField(required=False, default=False)
    
    def validate(self, data):
        new_start_date = data.get('new_start_date')
        new_end_date = data.get('new_end_date')
        
        if new_end_date <= new_start_date:
            raise serializers.ValidationError(
                "New end date must be after new start date"
            )
        
        if new_start_date <= timezone.now():
            raise serializers.ValidationError(
                "New start date must be in the future or current"
            )
        
        return data


class SubscriptionBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk subscription updates"""
    subscription_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    extend_days = serializers.IntegerField(min_value=0, max_value=365, required=False, default=0)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_subscription_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one subscription ID is required"
            )
        
        # Verify all subscriptions exist
        existing_count = UserSubscription.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError(
                f"Only {existing_count} out of {len(value)} subscriptions found"
            )
        
        return value
