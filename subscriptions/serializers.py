from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    SubscriptionPlan,
    UserSubscription,
    # Wallet,  # REMOVED - Replaced by PaymentTransaction
    # Transaction,  # REMOVED - Replaced by PaymentTransaction
    ConsultationVoucher,
    # ConsultationSession,  # REMOVED - Replaced by ConsultationBooking + CallSession
    DocumentType,
    DocumentPurchase,
    LearningMaterial,
    LearningMaterialPurchase,
    ConsultantEarnings,
    UploaderEarnings,
    Disbursement
)
from authentication.models import PolaUser


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    benefits_en = serializers.SerializerMethodField()
    benefits_sw = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    price_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'plan_type', 'name', 'name_sw', 'description', 'description_sw',
            'price', 'currency', 'price_details', 'duration_days', 'is_active', 
            'full_legal_library_access', 'monthly_questions_limit', 'free_documents_per_month', 
            'legal_updates', 'forum_access', 'student_hub_access', 'benefits_en', 
            'benefits_sw', 'permissions', 'created_at', 'updated_at'
        ]
    
    def get_benefits_en(self, obj):
        return obj.get_benefits_dict(language='en')
    
    def get_benefits_sw(self, obj):
        return obj.get_benefits_dict(language='sw')
    
    def get_permissions(self, obj):
        return obj.get_permissions()
    
    def get_price_details(self, obj):
        """Return formatted price object with currency"""
        currency_symbols = {
            'TZS': 'TSh',
            'USD': '$',
            'EUR': '€',
        }
        symbol = currency_symbols.get(obj.currency, obj.currency)
        
        # Format amount with thousands separator
        amount_str = f"{float(obj.price):,.2f}"
        
        return {
            'amount': str(obj.price),
            'currency': obj.currency,
            'currency_symbol': symbol,
            'formatted': f"{symbol} {amount_str}"
        }


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


# ============================================================================
# REMOVED SERIALIZERS - Wallet system replaced by PaymentTransaction  
# ============================================================================
# These serializers are commented out because the models were removed in Phase 1.
# They will be replaced with new serializers in Phase 2.
# See: docs/PHASE_1_COMPLETE_SUMMARY.md for details

# class WalletSerializer(serializers.ModelSerializer):
#     ... (lines 98-153 commented out - Wallet model removed)

# class TransactionSerializer(serializers.ModelSerializer):
#     ... (lines 156-189 commented out - Transaction model removed)

# class ConsultationSessionSerializer(serializers.ModelSerializer):
#     ... (lines 223-242 commented out - ConsultationSession model removed)

# class WalletDepositSerializer(serializers.Serializer):
#     ... (lines 325-333 commented out - Wallet model removed)

# class WalletWithdrawSerializer(serializers.Serializer):
#     ... (lines 335-343 commented out - Wallet model removed)

# ============================================================================
# END OF REMOVED SERIALIZERS
# ============================================================================


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


# ConsultationSessionSerializer REMOVED - ConsultationSession model no longer exists
# Use ConsultationBooking and CallSession models instead (Phase 2)


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


# ============================================================================
# REMOVED ACTION SERIALIZERS - Wallet and old Consultation system
# ============================================================================

# class WalletDepositSerializer(serializers.Serializer):
#     ... (Wallet deposits - replaced by PaymentTransaction in Phase 2)

# class WalletWithdrawSerializer(serializers.Serializer):
#     ... (Wallet withdrawals - replaced by PaymentTransaction in Phase 2)

# class BookConsultationSerializer(serializers.Serializer):
#     ... (Old consultation booking - replaced by ConsultationBookingSerializer in Phase 2)


class PurchaseVoucherSerializer(serializers.Serializer):
    """Serializer for purchasing consultation vouchers"""
    voucher_type = serializers.ChoiceField(choices=['mobile', 'physical'])
    duration_minutes = serializers.ChoiceField(choices=[5, 10, 20])
    payment_method = serializers.ChoiceField(
        choices=['wallet', 'mpesa', 'tigo_pesa', 'airtel_money'],
        default='wallet'
    )


# BookConsultationSerializer REMOVED - See Phase 2 for new ConsultationBookingSerializer


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


# ============================================================================
# DISBURSEMENT SERIALIZERS (Admin APIs)
# ============================================================================

class ConsultantEarningsSerializer(serializers.ModelSerializer):
    """Serializer for consultant earnings"""
    consultant_email = serializers.EmailField(source='consultant.email', read_only=True)
    consultant_name = serializers.CharField(source='consultant.full_name', read_only=True, allow_null=True)
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    
    class Meta:
        model = ConsultantEarnings
        fields = [
            'id', 'consultant', 'consultant_email', 'consultant_name',
            'booking', 'booking_reference', 'service_type',
            'gross_amount', 'platform_commission', 'net_earnings',
            'paid_out', 'payout_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UploaderEarningsSerializer(serializers.ModelSerializer):
    """Serializer for uploader earnings"""
    uploader_email = serializers.EmailField(source='uploader.email', read_only=True)
    uploader_name = serializers.CharField(source='uploader.full_name', read_only=True, allow_null=True)
    material_title = serializers.CharField(source='material.title', read_only=True, allow_null=True)
    
    class Meta:
        model = UploaderEarnings
        fields = [
            'id', 'uploader', 'uploader_email', 'uploader_name',
            'material', 'material_title', 'service_type',
            'gross_amount', 'platform_commission', 'net_earnings',
            'paid_out', 'payout_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DisbursementSerializer(serializers.ModelSerializer):
    """Serializer for disbursements (payouts)"""
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    recipient_full_name = serializers.CharField(source='recipient.full_name', read_only=True, allow_null=True)
    initiated_by_email = serializers.EmailField(source='initiated_by.email', read_only=True, allow_null=True)
    
    # Total earnings counts
    consultant_earnings_count = serializers.IntegerField(
        source='consultant_earnings.count', read_only=True
    )
    uploader_earnings_count = serializers.IntegerField(
        source='uploader_earnings.count', read_only=True
    )
    
    class Meta:
        model = Disbursement
        fields = [
            'id', 'recipient', 'recipient_email', 'recipient_full_name',
            'recipient_phone', 'recipient_name', 'disbursement_type',
            'amount', 'currency', 'payment_method', 'azampay_transaction_id',
            'external_reference', 'status', 'consultant_earnings_count',
            'uploader_earnings_count', 'initiated_by', 'initiated_by_email',
            'notes', 'failure_reason', 'initiated_at', 'processed_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'external_reference', 'azampay_transaction_id',
            'initiated_at', 'processed_at', 'completed_at'
        ]


class DisbursementDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for disbursements with related earnings"""
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    recipient_full_name = serializers.CharField(source='recipient.full_name', read_only=True, allow_null=True)
    initiated_by_email = serializers.EmailField(source='initiated_by.email', read_only=True, allow_null=True)
    
    # Related earnings
    consultant_earnings = ConsultantEarningsSerializer(many=True, read_only=True)
    uploader_earnings = UploaderEarningsSerializer(many=True, read_only=True)
    
    class Meta:
        model = Disbursement
        fields = [
            'id', 'recipient', 'recipient_email', 'recipient_full_name',
            'recipient_phone', 'recipient_name', 'disbursement_type',
            'amount', 'currency', 'payment_method', 'azampay_transaction_id',
            'external_reference', 'status', 'consultant_earnings',
            'uploader_earnings', 'initiated_by', 'initiated_by_email',
            'notes', 'failure_reason', 'initiated_at', 'processed_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'external_reference', 'azampay_transaction_id',
            'initiated_at', 'processed_at', 'completed_at'
        ]


class InitiateDisbursementSerializer(serializers.Serializer):
    """Serializer for initiating a disbursement"""
    recipient_id = serializers.IntegerField(required=True)
    disbursement_type = serializers.ChoiceField(
        choices=['consultant', 'uploader', 'refund', 'other'],
        required=True
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1000, required=True)
    payment_method = serializers.ChoiceField(
        choices=['tigo_pesa', 'airtel_money', 'mpesa', 'halopesa', 'bank_transfer'],
        required=True
    )
    recipient_phone = serializers.CharField(max_length=15, required=False, help_text="Phone number for mobile money (255XXXXXXXXX)")
    
    # Bank transfer fields
    bank_account_number = serializers.CharField(max_length=50, required=False, help_text="Bank account number")
    bank_code = serializers.CharField(max_length=20, required=False, help_text="Bank code/SWIFT code")
    bank_name = serializers.CharField(max_length=100, required=False, help_text="Bank name")
    recipient_name = serializers.CharField(max_length=255, required=False, help_text="Account holder name")
    verify_account = serializers.BooleanField(default=False, help_text="Verify account before creating disbursement")
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    # Optional: Link to specific earnings
    consultant_earnings_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    uploader_earnings_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    def validate_recipient_phone(self, value):
        """Validate and normalize phone number"""
        if value:
            from subscriptions.azampay_integration import format_phone_number
            return format_phone_number(value)
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Check if recipient exists
        recipient_id = data.get('recipient_id')
        try:
            recipient = PolaUser.objects.get(id=recipient_id)
            data['recipient'] = recipient
        except PolaUser.DoesNotExist:
            raise serializers.ValidationError("Recipient user not found")
        
        payment_method = data.get('payment_method')
        
        # Validate bank transfer fields
        if payment_method == 'bank_transfer':
            if not data.get('bank_account_number'):
                raise serializers.ValidationError("bank_account_number is required for bank transfers")
            if not data.get('bank_code'):
                raise serializers.ValidationError("bank_code is required for bank transfers")
            if not data.get('recipient_name'):
                raise serializers.ValidationError("recipient_name is required for bank transfers")
        else:
            # Mobile money requires phone number
            if not data.get('recipient_phone'):
                raise serializers.ValidationError("recipient_phone is required for mobile money transfers")
        
        # Validate earnings IDs if provided
        if data.get('consultant_earnings_ids'):
            earnings = ConsultantEarnings.objects.filter(
                id__in=data['consultant_earnings_ids'],
                consultant=recipient
            )
            if earnings.count() != len(data['consultant_earnings_ids']):
                raise serializers.ValidationError("Some consultant earnings not found or don't belong to recipient")
            data['consultant_earnings'] = earnings
        
        if data.get('uploader_earnings_ids'):
            earnings = UploaderEarnings.objects.filter(
                id__in=data['uploader_earnings_ids'],
                uploader=recipient
            )
            if earnings.count() != len(data['uploader_earnings_ids']):
                raise serializers.ValidationError("Some uploader earnings not found or don't belong to recipient")
            data['uploader_earnings'] = earnings
        
        return data


class EarningsSummarySerializer(serializers.Serializer):
    """Serializer for earnings summary"""
    user_id = serializers.IntegerField()
    user_email = serializers.EmailField()
    user_name = serializers.CharField()
    
    # Consultant earnings
    total_consultant_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_consultant_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    unpaid_consultant_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    consultant_earnings_count = serializers.IntegerField()
    
    # Uploader earnings
    total_uploader_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_uploader_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    unpaid_uploader_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    uploader_earnings_count = serializers.IntegerField()
    
    # Totals
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_unpaid = serializers.DecimalField(max_digits=12, decimal_places=2)
