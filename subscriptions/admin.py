from django.contrib import admin
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


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_days', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name', 'name_sw']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew']
    list_filter = ['status', 'plan', 'auto_renew']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'currency', 'total_earnings', 'total_withdrawn', 'is_active']
    list_filter = ['currency', 'is_active']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'status', 'reference', 'created_at']
    list_filter = ['transaction_type', 'status', 'payment_method']
    search_fields = ['reference', 'wallet__user__email', 'payment_reference']
    readonly_fields = ['created_at', 'updated_at', 'reference']
    date_hierarchy = 'created_at'


@admin.register(ConsultationVoucher)
class ConsultationVoucherAdmin(admin.ModelAdmin):
    list_display = ['user', 'voucher_type', 'duration_minutes', 'remaining_minutes', 
                    'amount_paid', 'status', 'expiry_date']
    list_filter = ['voucher_type', 'status']
    search_fields = ['user__email']
    readonly_fields = ['purchase_date', 'created_at', 'updated_at']
    date_hierarchy = 'purchase_date'


@admin.register(ConsultationSession)
class ConsultationSessionAdmin(admin.ModelAdmin):
    list_display = ['client', 'consultant', 'consultation_type', 'scheduled_date', 
                    'duration_minutes', 'total_amount', 'status']
    list_filter = ['consultation_type', 'status']
    search_fields = ['client__email', 'consultant__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'scheduled_date'


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'downloads_count', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'name_sw']
    readonly_fields = ['downloads_count', 'created_at', 'updated_at']


@admin.register(DocumentPurchase)
class DocumentPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'amount_paid', 'was_free', 
                    'download_count', 'purchase_date']
    list_filter = ['was_free', 'document_type__category']
    search_fields = ['user__email', 'document_type__name']
    readonly_fields = ['purchase_date', 'last_downloaded']
    date_hierarchy = 'purchase_date'


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploader', 'uploader_type', 'category', 'price', 
                    'downloads_count', 'total_revenue', 'is_approved', 'is_active']
    list_filter = ['uploader_type', 'category', 'is_approved', 'is_active']
    search_fields = ['title', 'uploader__email']
    readonly_fields = ['downloads_count', 'total_revenue', 'uploader_earnings', 
                       'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(LearningMaterialPurchase)
class LearningMaterialPurchaseAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'material', 'amount_paid', 'download_count', 'purchase_date']
    search_fields = ['buyer__email', 'material__title']
    readonly_fields = ['purchase_date', 'last_downloaded']
    date_hierarchy = 'purchase_date'
