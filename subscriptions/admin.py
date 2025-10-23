from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    # Subscription Models
    SubscriptionPlan,
    UserSubscription,
    
    # Consultant Models (NEW)
    ConsultantRegistrationRequest,
    ConsultantProfile,
    
    # Pricing Models (NEW)
    PricingConfiguration,
    
    # Consultation Models (NEW)
    CallCreditBundle,
    UserCallCredit,
    ConsultationBooking,
    CallSession,
    
    # Earnings Models (NEW)
    ConsultantEarnings,
    UploaderEarnings,
    
    # Document Models (NEW)
    GeneratedDocument,
    GeneratedDocumentPurchase,
    MaterialPurchase,
    
    # Payment Models (NEW)
    PaymentTransaction,
    
    # Legacy Models (Keep for backward compatibility)
    ConsultationVoucher,
    DocumentType,
    DocumentPurchase
)
from documents.models import LearningMaterial, LearningMaterialPurchase


# ============================================================================
# LEARNING MATERIAL ADMIN FORM
# ============================================================================

class LearningMaterialAdminForm(forms.ModelForm):
    """
    Custom form for creating news topics, discussions, and other content
    """
    class Meta:
        model = LearningMaterial
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., New Legal Reform on Contract Law',
                'style': 'width: 100%;'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Brief summary of the news/topic (shown in previews)',
                'rows': 3,
                'style': 'width: 100%;'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': 'Full content/article. You can use HTML or Markdown formatting.',
                'rows': 15,
                'style': 'width: 100%; font-family: monospace;'
            }),
        }
        help_texts = {
            'hub_type': '🎯 Select where to post: Advocates (news/discussions), Forum (community), Legal Ed (education)',
            'content_type': '📝 News/Announcement for important updates, Discussion for topics to debate',
            'price': '💰 Leave as 0 for free content (news/discussions). Only set price for downloadable documents.',
            'is_pinned': '📌 Pin to keep at top of the feed',
            'is_approved': '✅ Auto-approved for admin-created content',
            'is_active': '🟢 Make visible to users immediately',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set helpful defaults for new content
        if not self.instance.pk:
            self.fields['price'].initial = 0
            self.fields['is_approved'].initial = True
            self.fields['is_active'].initial = True
            self.fields['is_downloadable'].initial = False
            self.fields['language'].initial = 'en'
        
        # Make some fields not required for news/discussions
        self.fields['file'].required = False
        self.fields['subtopic'].required = False
        
        # Add CSS classes for better UI
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.Select)):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' vTextField'


# ============================================================================
# SUBSCRIPTION ADMIN
# ============================================================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'currency', 'duration_days', 'is_active']
    list_filter = ['plan_type', 'is_active', 'currency']
    search_fields = ['name', 'name_sw']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('plan_type', 'name', 'name_sw', 'description', 'description_sw')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'duration_days', 'is_active')
        }),
        ('Features', {
            'fields': (
                'full_legal_library_access',
                'monthly_questions_limit',
                'free_documents_per_month',
                'legal_updates',
                'forum_access',
                'student_hub_access'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'plan', 'status', 'start_date', 'end_date', 
        'days_remaining', 'auto_renew'
    ]
    list_filter = ['status', 'plan', 'auto_renew']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'start_date']
    date_hierarchy = 'start_date'
    
    def days_remaining(self, obj):
        days = obj.days_remaining()
        if days > 7:
            color = 'green'
        elif days > 3:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{} days</span>',
            color, days
        )
    days_remaining.short_description = 'Days Left'


# ============================================================================
# CONSULTANT REGISTRATION & APPROVAL ADMIN (NEW)
# ============================================================================

@admin.register(ConsultantRegistrationRequest)
class ConsultantRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'consultant_type', 'get_email', 
        'get_experience', 'status', 'created_at', 'reviewed_at'
    ]
    list_filter = ['status', 'consultant_type', 'offers_mobile_consultations', 'offers_physical_consultations']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 
        'user__roll_number', 'user__bar_membership_number'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'reviewed_at', 'reviewed_by',
        'get_professional_info_display', 'get_specializations_display'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'consultant_type')
        }),
        ('Professional Information (from PolaUser)', {
            'fields': ('get_professional_info_display', 'get_specializations_display'),
            'description': 'Professional data is stored in the PolaUser model'
        }),
        ('Documents', {
            'fields': (
                'license_document',
                'id_document',
                'cv_document',
                'additional_documents'
            )
        }),
        ('Service Preferences', {
            'fields': (
                'offers_mobile_consultations',
                'offers_physical_consultations',
                'preferred_consultation_city'
            )
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_experience(self, obj):
        return f"{obj.user.years_of_experience or 0} years"
    get_experience.short_description = 'Experience'
    
    def get_professional_info_display(self, obj):
        """Display professional info from PolaUser"""
        info = obj.get_professional_info()
        html = f"""
        <div style="line-height: 1.8;">
            <strong>Email:</strong> {info['email']}<br>
            <strong>Phone:</strong> {info['phone'] or 'N/A'}<br>
            <strong>Experience:</strong> {info['years_of_experience'] or 0} years<br>
            <strong>Roll Number:</strong> {info['roll_number'] or 'N/A'}<br>
            <strong>Bar Membership:</strong> {info['bar_membership_number'] or 'N/A'}<br>
        </div>
        """
        return format_html(html)
    get_professional_info_display.short_description = 'Professional Details'
    
    def get_specializations_display(self, obj):
        """Display specializations from PolaUser"""
        info = obj.get_professional_info()
        specializations = info['specializations']
        if specializations:
            specs_html = '<br>'.join([f"• {spec}" for spec in specializations])
            return format_html(f'<div style="line-height: 1.8;">{specs_html}</div>')
        return format_html('<em style="color: #999;">No specializations listed</em>')
    get_specializations_display.short_description = 'Areas of Specialization'
    
    def get_user_phone(self, obj):
        if hasattr(obj.user, 'contact'):
            return obj.user.contact.phone_number
        return 'N/A'
    get_user_phone.short_description = 'Phone (from user)'
    
    def approve_requests(self, request, queryset):
        for obj in queryset.filter(status='pending'):
            obj.approve(request.user)
        self.message_user(request, f"{queryset.count()} requests approved successfully.")
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        for obj in queryset.filter(status='pending'):
            obj.reject(request.user, "Rejected via bulk action")
        self.message_user(request, f"{queryset.count()} requests rejected.")
    reject_requests.short_description = "Reject selected requests"


@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'consultant_type', 'city',
        'total_consultations', 'total_earnings', 'average_rating',
        'is_available'
    ]
    list_filter = ['consultant_type', 'is_available', 'offers_mobile_consultations', 'offers_physical_consultations']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'specialization']
    readonly_fields = [
        'registration_request', 'total_consultations', 'total_earnings',
        'average_rating', 'total_reviews', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Consultant Information', {
            'fields': ('user', 'registration_request', 'consultant_type')
        }),
        ('Professional Details', {
            'fields': ('specialization', 'years_of_experience')
        }),
        ('Service Offerings', {
            'fields': (
                'offers_mobile_consultations',
                'offers_physical_consultations',
                'city',
                'is_available'
            )
        }),
        ('Statistics', {
            'fields': (
                'total_consultations',
                'total_earnings',
                'average_rating',
                'total_reviews'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'


# ============================================================================
# PRICING CONFIGURATION ADMIN (NEW)
# ============================================================================

@admin.register(PricingConfiguration)
class PricingConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'service_type', 'price', 'platform_commission_percent',
        'consultant_share_percent', 'is_active'
    ]
    list_filter = ['is_active', 'service_type']
    search_fields = ['service_type', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_type', 'price', 'description', 'is_active')
        }),
        ('Revenue Split', {
            'fields': ('platform_commission_percent', 'consultant_share_percent'),
            'description': 'Default is 60% platform / 40% consultant'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# CONSULTATION & BOOKING ADMIN (NEW)
# ============================================================================

@admin.register(CallCreditBundle)
class CallCreditBundleAdmin(admin.ModelAdmin):
    list_display = ['name', 'minutes', 'price', 'validity_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserCallCredit)
class UserCallCreditAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'bundle', 'remaining_minutes', 'total_minutes',
        'status', 'expiry_date'
    ]
    list_filter = ['status', 'bundle']
    search_fields = ['user__email']
    readonly_fields = ['purchase_date', 'total_minutes']
    date_hierarchy = 'purchase_date'


@admin.register(ConsultationBooking)
class ConsultationBookingAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'consultant', 'booking_type', 'scheduled_date',
        'status', 'total_amount', 'consultant_earnings'
    ]
    list_filter = ['booking_type', 'status']
    search_fields = ['client__email', 'consultant__email']
    readonly_fields = ['created_at', 'updated_at', 'actual_duration_minutes']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Participants', {
            'fields': ('client', 'consultant')
        }),
        ('Booking Details', {
            'fields': (
                'booking_type',
                'status',
                'scheduled_date',
                'scheduled_duration_minutes'
            )
        }),
        ('Actual Session', {
            'fields': (
                'actual_start_time',
                'actual_end_time',
                'actual_duration_minutes'
            )
        }),
        ('Pricing', {
            'fields': ('total_amount', 'platform_commission', 'consultant_earnings')
        }),
        ('Additional Info', {
            'fields': ('meeting_location', 'client_notes', 'consultant_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ['booking', 'start_time', 'duration_minutes', 'call_quality_rating']
    list_filter = ['call_quality_rating']
    search_fields = ['booking__client__email', 'booking__consultant__email']
    readonly_fields = ['created_at', 'duration_minutes']
    date_hierarchy = 'start_time'


# ============================================================================
# EARNINGS ADMIN (NEW)
# ============================================================================

@admin.register(ConsultantEarnings)
class ConsultantEarningsAdmin(admin.ModelAdmin):
    list_display = [
        'consultant', 'service_type', 'gross_amount',
        'platform_commission', 'net_earnings', 'paid_out', 'created_at'
    ]
    list_filter = ['service_type', 'paid_out']
    search_fields = ['consultant__email']
    readonly_fields = ['created_at', 'booking']
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_paid']
    
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        queryset.update(paid_out=True, payout_date=timezone.now())
        self.message_user(request, f"{queryset.count()} earnings marked as paid.")
    mark_as_paid.short_description = "Mark selected as paid out"


@admin.register(UploaderEarnings)
class UploaderEarningsAdmin(admin.ModelAdmin):
    list_display = [
        'uploader', 'service_type', 'gross_amount',
        'platform_commission', 'net_earnings', 'paid_out', 'created_at'
    ]
    list_filter = ['service_type', 'paid_out']
    search_fields = ['uploader__email']
    readonly_fields = ['created_at', 'material']
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_paid']
    
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        queryset.update(paid_out=True, payout_date=timezone.now())
        self.message_user(request, f"{queryset.count()} earnings marked as paid.")
    mark_as_paid.short_description = "Mark selected as paid out"


# ============================================================================
# DOCUMENT & MATERIAL ADMIN (NEW)
# ============================================================================

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'document_type', 'was_free', 'created_at']
    list_filter = ['document_type', 'was_free']
    search_fields = ['title', 'user__email']
    readonly_fields = ['created_at', 'template_used']
    date_hierarchy = 'created_at'


@admin.register(GeneratedDocumentPurchase)
class GeneratedDocumentPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'document', 'amount_paid', 'payment_method', 'created_at']
    list_filter = ['payment_method']
    search_fields = ['user__email', 'document__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(MaterialPurchase)
class MaterialPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'buyer', 'material', 'amount_paid', 'platform_commission',
        'uploader_earnings', 'download_count', 'created_at'
    ]
    search_fields = ['buyer__email', 'material__title']
    readonly_fields = ['created_at', 'last_downloaded']
    date_hierarchy = 'created_at'


# ============================================================================
# PAYMENT TRANSACTION ADMIN (NEW)
# ============================================================================

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'transaction_type', 'amount', 'payment_method',
        'status', 'payment_reference', 'created_at'
    ]
    list_filter = ['transaction_type', 'status', 'payment_method']
    search_fields = ['payment_reference', 'gateway_reference', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'payment_reference']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'transaction_type', 'amount', 'currency', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'gateway_reference')
        }),
        ('Related Objects', {
            'fields': ('related_subscription', 'related_booking')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# LEGACY MODELS ADMIN (Keep for backward compatibility)
# ============================================================================


@admin.register(ConsultationVoucher)
class ConsultationVoucherAdmin(admin.ModelAdmin):
    list_display = ['user', 'voucher_type', 'duration_minutes', 'remaining_minutes', 
                    'amount_paid', 'status', 'expiry_date']
    list_filter = ['voucher_type', 'status']
    search_fields = ['user__email']
    readonly_fields = ['purchase_date', 'created_at', 'updated_at']
    date_hierarchy = 'purchase_date'


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
    """
    Admin for unified content model (posts + documents across all hubs)
    
    Admins can create:
    - News topics for Advocates Hub
    - Discussion topics for Forum
    - Announcements for all hubs
    - Articles and educational content
    """
    form = LearningMaterialAdminForm
    
    list_display = ['title', 'hub_type', 'content_type', 'uploader', 'uploader_type', 
                    'price', 'downloads_count', 'views_count', 'total_revenue', 
                    'is_pinned', 'is_approved', 'is_active', 'created_at']
    list_filter = ['hub_type', 'content_type', 'uploader_type', 'is_approved', 
                   'is_active', 'is_pinned', 'is_downloadable', 'language', 'created_at']
    search_fields = ['title', 'description', 'content', 'uploader__email', 
                     'uploader__first_name', 'uploader__last_name']
    readonly_fields = ['downloads_count', 'views_count', 'total_revenue', 'uploader_earnings', 
                       'platform_earnings', 'created_at', 'updated_at', 'engagement_stats', 'admin_guide']
    date_hierarchy = 'created_at'
    ordering = ['-is_pinned', '-created_at']
    list_per_page = 50
    save_on_top = True
    
    # Allow filtering by multiple fields in admin
    list_filter = (
        'hub_type',
        'content_type',
        'uploader_type',
        'is_approved',
        'is_active',
        'is_pinned',
        'is_downloadable',
        'language',
        ('created_at', admin.DateFieldListFilter),
    )
    
    fieldsets = (
        ('📖 Quick Guide', {
            'fields': ('admin_guide',),
            'classes': ('collapse',),
            'description': 'Instructions for creating news topics and discussions'
        }),
        ('🎯 Hub & Content Type', {
            'fields': ('hub_type', 'content_type', 'uploader', 'uploader_type'),
            'description': 'Select the hub and content type. For news/discussions, choose "news", "discussion", or "announcement".'
        }),
        ('📝 Content Information', {
            'fields': ('title', 'description', 'content'),
            'description': 'Main content. Use the content field for rich text (HTML/Markdown supported).'
        }),
        ('📎 Attachments (Optional)', {
            'fields': ('file', 'file_size', 'video_url'),
            'classes': ('collapse',),
            'description': 'Optional: Attach files or add video links to your news/discussion topic.'
        }),
        ('🏷️ Categorization', {
            'fields': ('subtopic', 'language'),
            'classes': ('collapse',),
            'description': 'Optional: Link to Legal Education subtopic if relevant.'
        }),
        ('💰 Pricing & Revenue (For Documents)', {
            'fields': ('price', 'is_downloadable', 'downloads_count', 'views_count',
                      'total_revenue', 'uploader_earnings', 'platform_earnings'),
            'classes': ('collapse',),
            'description': 'Pricing only applies to downloadable documents (Students Hub). News/discussions are always free.'
        }),
        ('⚙️ Settings & Moderation', {
            'fields': ('is_approved', 'is_active', 'is_pinned'),
            'description': 'Pin important news/announcements to keep them at the top.'
        }),
        ('📊 Engagement Statistics', {
            'fields': ('engagement_stats',),
            'classes': ('collapse',),
            'description': 'View comments, likes, and bookmarks for this content.'
        }),
        ('🕐 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def admin_guide(self, obj):
        """Display quick guide for admins"""
        guide_html = """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; margin: 10px 0;">
            <h2 style="margin-top: 0; color: white;">📰 Quick Guide: Creating News & Discussion Topics</h2>
            
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #ffd700;">🗞️ Creating News (Advocates Hub)</h3>
                <ol style="line-height: 2;">
                    <li><strong>Hub Type:</strong> Select "Advocates Hub"</li>
                    <li><strong>Content Type:</strong> Choose "News" or "Announcement"</li>
                    <li><strong>Title:</strong> Eye-catching headline (e.g., "Supreme Court Rules on New Evidence Act")</li>
                    <li><strong>Description:</strong> Brief summary (shown in feed previews)</li>
                    <li><strong>Content:</strong> Full article with details</li>
                    <li><strong>Pin It:</strong> Check "is_pinned" for important breaking news</li>
                </ol>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #98fb98;">💬 Creating Discussion Topics (Forum)</h3>
                <ol style="line-height: 2;">
                    <li><strong>Hub Type:</strong> Select "Community Forum"</li>
                    <li><strong>Content Type:</strong> Choose "Discussion" or "Question"</li>
                    <li><strong>Title:</strong> Question or topic to debate (e.g., "Should contract law be reformed?")</li>
                    <li><strong>Description:</strong> Context for the discussion</li>
                    <li><strong>Content:</strong> Detailed explanation or opening statement</li>
                    <li><strong>Engage:</strong> Users will comment and discuss below</li>
                </ol>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #87ceeb;">📢 Creating Announcements (All Hubs)</h3>
                <ol style="line-height: 2;">
                    <li><strong>Hub Type:</strong> Select any hub (Advocates/Students/Forum/Legal Ed)</li>
                    <li><strong>Content Type:</strong> Choose "Announcement"</li>
                    <li><strong>Title:</strong> Clear announcement (e.g., "Platform Maintenance on Friday")</li>
                    <li><strong>Pin It:</strong> Always pin important announcements</li>
                    <li><strong>Active:</strong> Uncheck "is_active" when announcement is no longer relevant</li>
                </ol>
            </div>
            
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: white;">💡 Pro Tips</h3>
                <ul style="line-height: 2;">
                    <li>✅ News/discussions are <strong>always FREE</strong> (price = 0)</li>
                    <li>📌 Pin urgent/important content to keep at top</li>
                    <li>🎯 Use clear, engaging titles to attract readers</li>
                    <li>📝 Add rich content with HTML formatting for better readability</li>
                    <li>🔗 Optionally attach files or add video links for multimedia content</li>
                    <li>📊 Check engagement stats to see how users interact</li>
                    <li>🟢 Content is auto-approved and active for admin-created posts</li>
                </ul>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 15px;">
                <strong>📋 Common Content Types:</strong><br>
                <span style="display: inline-block; margin: 5px; padding: 5px 10px; background: #28a745; border-radius: 3px;">News</span>
                <span style="display: inline-block; margin: 5px; padding: 5px 10px; background: #17a2b8; border-radius: 3px;">Discussion</span>
                <span style="display: inline-block; margin: 5px; padding: 5px 10px; background: #ffc107; border-radius: 3px;">Announcement</span>
                <span style="display: inline-block; margin: 5px; padding: 5px 10px; background: #6f42c1; border-radius: 3px;">Article</span>
                <span style="display: inline-block; margin: 5px; padding: 5px 10px; background: #e83e8c; border-radius: 3px;">Question</span>
            </div>
        </div>
        """
        return format_html(guide_html)
    admin_guide.short_description = 'Admin Guide'
    
    def engagement_stats(self, obj):
        """Display engagement statistics"""
        if obj.pk:
            from django.db.models import Count
            stats = {
                'comments': obj.hubcomment_set.count(),
                'likes': obj.contentlike_set.count(),
                'bookmarks': obj.contentbookmark_set.count(),
            }
            html = f"""
            <div style="line-height: 2; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                <strong style="color: #007bff;">💬 Comments:</strong> {stats['comments']}<br>
                <strong style="color: #dc3545;">❤️ Likes:</strong> {stats['likes']}<br>
                <strong style="color: #28a745;">🔖 Bookmarks:</strong> {stats['bookmarks']}<br>
                <strong style="color: #6c757d;">👁️ Views:</strong> {obj.views_count}<br>
                <hr style="margin: 10px 0;">
                <strong>Engagement Score:</strong> {(stats['likes'] * 2) + (stats['comments'] * 3) + (stats['bookmarks'] * 4)}
            </div>
            """
            return format_html(html)
        return format_html('<em>Save to see engagement statistics</em>')
    engagement_stats.short_description = 'Engagement'
    
    def save_model(self, request, obj, form, change):
        """Auto-set uploader to current admin user if not set"""
        if not change:  # Only on creation
            if not obj.uploader:
                obj.uploader = request.user
            if not obj.uploader_type:
                obj.uploader_type = 'admin'
        super().save_model(request, obj, form, change)
    
    # Admin Actions
    actions = ['pin_content', 'unpin_content', 'approve_content', 'activate_content', 'deactivate_content']
    
    def pin_content(self, request, queryset):
        """Pin selected content to top of feed"""
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} item(s) pinned successfully.')
    pin_content.short_description = '📌 Pin selected content'
    
    def unpin_content(self, request, queryset):
        """Unpin selected content"""
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} item(s) unpinned.')
    unpin_content.short_description = '📍 Unpin selected content'
    
    def approve_content(self, request, queryset):
        """Approve selected content"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} item(s) approved.')
    approve_content.short_description = '✅ Approve selected content'
    
    def activate_content(self, request, queryset):
        """Activate selected content"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} item(s) activated.')
    activate_content.short_description = '🟢 Activate selected content'
    
    def deactivate_content(self, request, queryset):
        """Deactivate selected content"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} item(s) deactivated.')
    deactivate_content.short_description = '🔴 Deactivate selected content'


@admin.register(LearningMaterialPurchase)
class LearningMaterialPurchaseAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'material', 'amount_paid', 'download_count', 'purchase_date']
    search_fields = ['buyer__email', 'material__title']
    readonly_fields = ['purchase_date', 'last_downloaded']
    date_hierarchy = 'purchase_date'
