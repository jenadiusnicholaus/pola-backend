from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    SubscriptionPlan,
    UserSubscription,
    Wallet,
    Transaction,
    ConsultationVoucher,
    ConsultationSession,
    DocumentType,
    DocumentPurchase,
    LearningMaterial,
    LearningMaterialPurchase
)
from authentication.models import PolaUser


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    benefits_en = serializers.SerializerMethodField()
    benefits_sw = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'plan_type', 'name', 'name_sw', 'description', 'description_sw',
            'price', 'duration_days', 'is_active', 'full_legal_library_access',
            'monthly_questions_limit', 'free_documents_per_month', 'legal_updates',
            'forum_access', 'student_hub_access', 'benefits_en', 'benefits_sw',
            'permissions'
        ]
    
    def get_benefits_en(self, obj):
        return obj.get_benefits_dict(language='en')
    
    def get_benefits_sw(self, obj):
        return obj.get_benefits_dict(language='sw')
    
    def get_permissions(self, obj):
        return obj.get_permissions()


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_active_status = serializers.BooleanField(source='is_active', read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_trial_status = serializers.BooleanField(source='is_trial', read_only=True)
    can_ask_more_questions = serializers.SerializerMethodField()
    can_generate_free_doc = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'user_email', 'plan', 'plan_details', 'status',
            'start_date', 'end_date', 'auto_renew', 'questions_asked_this_month',
            'documents_generated_this_month', 'is_active_status', 'days_remaining',
            'is_trial_status', 'can_ask_more_questions', 'can_generate_free_doc',
            'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'start_date', 'created_at', 'updated_at']
    
    def get_can_ask_more_questions(self, obj):
        return obj.can_ask_question()
    
    def get_can_generate_free_doc(self, obj):
        return obj.can_generate_free_document()
    
    def get_permissions(self, obj):
        return obj.get_permissions()


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    available_for_withdrawal = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'user_email', 'balance', 'currency', 'is_active',
            'total_earnings', 'total_withdrawn', 'available_for_withdrawal',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'balance', 'total_earnings', 'total_withdrawn', 'created_at', 'updated_at']
    
    def get_available_for_withdrawal(self, obj):
        # Balance that can be withdrawn (earnings - already withdrawn)
        return float(obj.balance)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    wallet_user = serializers.EmailField(source='wallet.user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'wallet_user', 'transaction_type', 'amount', 'status',
            'reference', 'description', 'payment_method', 'payment_reference',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'created_at', 'updated_at']


class ConsultationVoucherSerializer(serializers.ModelSerializer):
    """Serializer for consultation vouchers"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_active_status = serializers.BooleanField(source='is_active', read_only=True)
    pricing_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultationVoucher
        fields = [
            'id', 'user', 'user_email', 'voucher_type', 'duration_minutes',
            'remaining_minutes', 'amount_paid', 'purchase_date', 'expiry_date',
            'status', 'sessions_count', 'is_active_status', 'pricing_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'purchase_date', 'sessions_count', 'created_at', 'updated_at']
    
    def get_pricing_details(self, obj):
        return obj.get_pricing_details()


class ConsultantSerializer(serializers.ModelSerializer):
    """Simplified serializer for consultants"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='user_role.get_role_display', read_only=True)
    
    class Meta:
        model = PolaUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role_display']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class ConsultationSessionSerializer(serializers.ModelSerializer):
    """Serializer for consultation sessions"""
    client_details = ConsultantSerializer(source='client', read_only=True)
    consultant_details = ConsultantSerializer(source='consultant', read_only=True)
    actual_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultationSession
        fields = [
            'id', 'client', 'client_details', 'consultant', 'consultant_details',
            'consultation_type', 'scheduled_date', 'start_time', 'end_time',
            'duration_minutes', 'actual_duration', 'total_amount', 'consultant_share',
            'app_share', 'voucher', 'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['start_time', 'end_time', 'duration_minutes', 'created_at', 'updated_at']
    
    def get_actual_duration(self, obj):
        if obj.start_time and obj.end_time:
            return int((obj.end_time - obj.start_time).total_seconds() / 60)
        return 0


class DocumentTypeSerializer(serializers.ModelSerializer):
    """Serializer for document types"""
    
    class Meta:
        model = DocumentType
        fields = [
            'id', 'category', 'name', 'name_sw', 'description', 'description_sw',
            'price', 'template_path', 'required_fields', 'is_active',
            'downloads_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['downloads_count', 'created_at', 'updated_at']


class DocumentPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for document purchases"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    document_details = DocumentTypeSerializer(source='document_type', read_only=True)
    
    class Meta:
        model = DocumentPurchase
        fields = [
            'id', 'user', 'user_email', 'document_type', 'document_details',
            'amount_paid', 'was_free', 'generated_file', 'document_data',
            'download_count', 'last_downloaded', 'purchase_date'
        ]
        read_only_fields = ['user', 'download_count', 'last_downloaded', 'purchase_date']


class LearningMaterialSerializer(serializers.ModelSerializer):
    """Serializer for learning materials"""
    uploader_email = serializers.EmailField(source='uploader.email', read_only=True)
    uploader_name = serializers.SerializerMethodField()
    revenue_split_info = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningMaterial
        fields = [
            'id', 'uploader', 'uploader_email', 'uploader_name', 'uploader_type',
            'title', 'description', 'category', 'file', 'file_size', 'price',
            'downloads_count', 'total_revenue', 'uploader_earnings',
            'revenue_split_info', 'is_approved', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'uploader', 'downloads_count', 'total_revenue', 'uploader_earnings',
            'is_approved', 'created_at', 'updated_at'
        ]
    
    def get_uploader_name(self, obj):
        return f"{obj.uploader.first_name} {obj.uploader.last_name}"
    
    def get_revenue_split_info(self, obj):
        split = obj.get_revenue_split()
        return {
            'uploader_percentage': int(split['uploader'] * 100),
            'app_percentage': int(split['app'] * 100),
            'uploader_gets': float(obj.price * Decimal(str(split['uploader']))),
            'app_gets': float(obj.price * Decimal(str(split['app'])))
        }


class LearningMaterialPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for learning material purchases"""
    buyer_email = serializers.EmailField(source='buyer.email', read_only=True)
    material_details = LearningMaterialSerializer(source='material', read_only=True)
    
    class Meta:
        model = LearningMaterialPurchase
        fields = [
            'id', 'buyer', 'buyer_email', 'material', 'material_details',
            'amount_paid', 'purchase_date', 'download_count', 'last_downloaded'
        ]
        read_only_fields = ['buyer', 'download_count', 'last_downloaded', 'purchase_date']


# Input Serializers for Actions

class SubscribeSerializer(serializers.Serializer):
    """Serializer for subscribing to a plan"""
    plan_id = serializers.IntegerField(required=True)
    auto_renew = serializers.BooleanField(default=False)
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'mpesa', 'tigo_pesa', 'airtel_money', 'card'],
        default='wallet'
    )


class WalletDepositSerializer(serializers.Serializer):
    """Serializer for wallet deposits"""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=100)
    payment_method = serializers.ChoiceField(
        choices=['mpesa', 'tigo_pesa', 'airtel_money', 'card'],
        required=True
    )
    phone_number = serializers.CharField(max_length=15, required=False)


class WalletWithdrawSerializer(serializers.Serializer):
    """Serializer for wallet withdrawals"""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1000)
    withdrawal_method = serializers.ChoiceField(
        choices=['mpesa', 'tigo_pesa', 'airtel_money', 'bank'],
        required=True
    )
    account_number = serializers.CharField(max_length=50, required=True)


class PurchaseVoucherSerializer(serializers.Serializer):
    """Serializer for purchasing consultation vouchers"""
    voucher_type = serializers.ChoiceField(choices=['mobile', 'physical'])
    duration_minutes = serializers.ChoiceField(choices=[5, 10, 20])
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'mpesa', 'tigo_pesa', 'airtel_money'],
        default='wallet'
    )


class BookConsultationSerializer(serializers.Serializer):
    """Serializer for booking a consultation"""
    consultant_id = serializers.IntegerField(required=True)
    consultation_type = serializers.ChoiceField(choices=['mobile', 'physical'])
    scheduled_date = serializers.DateTimeField(required=True)
    voucher_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class PurchaseDocumentSerializer(serializers.Serializer):
    """Serializer for purchasing documents"""
    document_type_id = serializers.IntegerField(required=True)
    document_data = serializers.JSONField(required=True)
    use_free_monthly = serializers.BooleanField(default=False)
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'mpesa', 'tigo_pesa'],
        default='wallet'
    )


class UploadLearningMaterialSerializer(serializers.Serializer):
    """Serializer for uploading learning materials"""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    category = serializers.ChoiceField(
        choices=['notes', 'past_papers', 'assignments', 'tutorials', 'other']
    )
    file = serializers.FileField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1000)


class PurchaseLearningMaterialSerializer(serializers.Serializer):
    """Serializer for purchasing learning materials"""
    material_id = serializers.IntegerField(required=True)
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'mpesa', 'tigo_pesa'],
        default='wallet'
    )
