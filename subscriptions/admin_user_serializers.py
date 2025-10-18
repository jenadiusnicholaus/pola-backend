"""
Admin User Management Serializers
Handles user listing, details, and management
"""

from rest_framework import serializers
from authentication.models import PolaUser, Contact, Address
from django.db.models import Count, Sum, Q
from decimal import Decimal


class UserContactSerializer(serializers.ModelSerializer):
    """Nested serializer for user contact info"""
    class Meta:
        model = Contact
        fields = ['phone_number', 'phone_is_verified', 'alternative_phone_number']
        ref_name = 'AdminUserContact'


class UserAddressSerializer(serializers.ModelSerializer):
    """Nested serializer for user address"""
    class Meta:
        model = Address
        fields = ['street_address', 'city', 'state', 'postal_code', 'country']
        ref_name = 'AdminUserAddress'


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view"""
    role_name = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    total_subscriptions = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = PolaUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role_name',
            'phone_number', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'total_subscriptions', 'is_verified'
        ]
        ref_name = 'AdminUserList'
    
    def get_role_name(self, obj):
        """Get user role name"""
        try:
            return obj.user_role.role_name if obj.user_role else None
        except:
            return None
    
    def get_phone_number(self, obj):
        """Get phone number from Contact model"""
        try:
            return obj.contact.phone_number
        except:
            return None
    
    def get_total_subscriptions(self, obj):
        """Count user subscriptions"""
        from .models import UserSubscription
        return UserSubscription.objects.filter(user=obj).count()
    
    def get_is_verified(self, obj):
        """Check if user is verified"""
        try:
            return obj.contact.phone_is_verified if hasattr(obj, 'contact') else False
        except:
            return False
    
    def to_representation(self, instance):
        """Ensure all numeric fields are JSON-compliant"""
        data = super().to_representation(instance)
        
        # Sanitize all float/decimal fields to prevent infinity
        for key, value in data.items():
            if isinstance(value, (int, float)):
                try:
                    # Check for infinity or NaN
                    if value == float('inf') or value == float('-inf') or value != value:
                        data[key] = 0
                except (ValueError, TypeError):
                    pass
        
        return data


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single user view"""
    role_name = serializers.SerializerMethodField()
    contact = UserContactSerializer(read_only=True)
    address = UserAddressSerializer(read_only=True)
    subscription_stats = serializers.SerializerMethodField()
    transaction_stats = serializers.SerializerMethodField()
    consultation_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = PolaUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role_name',
            'date_of_birth', 'gender', 'profile_picture',
            'is_active', 'is_staff', 'is_superuser', 'agreed_to_Terms',
            'date_joined', 'last_login',
            'contact', 'address',
            'subscription_stats', 'transaction_stats', 'consultation_stats'
        ]
        ref_name = 'AdminUserDetail'
    
    def get_role_name(self, obj):
        """Get user role name"""
        try:
            return obj.user_role.role_name if obj.user_role else None
        except:
            return None
    
    def get_subscription_stats(self, obj):
        """Get subscription statistics"""
        from .models import UserSubscription
        subscriptions = UserSubscription.objects.filter(user=obj)
        
        return {
            'total': subscriptions.count(),
            'active': subscriptions.filter(status='active').count(),
            'expired': subscriptions.filter(status='expired').count(),
            'cancelled': subscriptions.filter(status='cancelled').count(),
        }
    
    def get_transaction_stats(self, obj):
        """Get transaction statistics"""
        from .models import PaymentTransaction
        transactions = PaymentTransaction.objects.filter(user=obj)
        
        total_spent = transactions.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        return {
            'total_transactions': transactions.count(),
            'completed': transactions.filter(status='completed').count(),
            'pending': transactions.filter(status='pending').count(),
            'failed': transactions.filter(status='failed').count(),
            'total_spent': float(total_spent),
        }
    
    def get_consultation_stats(self, obj):
        """Get consultation statistics"""
        from .models import ConsultationBooking
        
        as_client = ConsultationBooking.objects.filter(client=obj)
        as_consultant = ConsultationBooking.objects.filter(consultant=obj)
        
        return {
            'as_client': {
                'total': as_client.count(),
                'completed': as_client.filter(status='completed').count(),
            },
            'as_consultant': {
                'total': as_consultant.count(),
                'completed': as_consultant.filter(status='completed').count(),
            }
        }
    
    def to_representation(self, instance):
        """Ensure all numeric fields are JSON-compliant"""
        data = super().to_representation(instance)
        
        # Sanitize all float/decimal fields to prevent infinity
        def sanitize_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    sanitize_dict(value)
                elif isinstance(value, (int, float)):
                    try:
                        # Check for infinity or NaN
                        if value == float('inf') or value == float('-inf') or value != value:
                            d[key] = 0
                    except (ValueError, TypeError):
                        pass
        
        sanitize_dict(data)
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user"""
    class Meta:
        model = PolaUser
        fields = [
            'first_name', 'last_name', 'is_active', 'is_staff',
        ]
        ref_name = 'AdminUserUpdate'


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    staff_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    users_with_subscriptions = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    new_users_this_week = serializers.IntegerField()
    
    # By role
    users_by_role = serializers.DictField()
