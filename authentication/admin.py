from django.contrib import admin
from .models import (
    AcademicRole, LegalSpecialization, PlaceOfWork, UserRole, RolePermission,
    Contact, Address, Verification, VerificationDocument, Document, PolaUser,
    Region, District, OperatingRegion, OperatingDistrict, Specialization,
    ProfessionalSpecialization, RegionalChapter, DeviceToken, NotificationPreference
)
from .device_models import UserDevice, UserSession, LoginHistory, SecurityAlert
from .device_models import UserDevice, UserSession, LoginHistory, SecurityAlert

@admin.register(PolaUser)
class PolaUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'roll_number', 'bar_membership_number')
    list_filter = ('user_role', 'is_active', 'is_staff', 'is_superuser', 'gender', 'practice_status')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'first_name', 'last_name', 'date_of_birth', 'gender', 'profile_picture')
        }),
        ('Role & Permissions', {
            'fields': ('user_role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Professional Information', {
            'fields': ('roll_number', 'bar_membership_number', 'practice_status', 'years_of_experience', 
                      'year_established', 'regional_chapter', 'place_of_work', 'associated_law_firm')
        }),
        ('Law Firm Information', {
            'fields': ('firm_name', 'managing_partner', 'number_of_lawyers')
        }),
        ('Academic Information', {
            'fields': ('university_name', 'academic_role', 'year_of_study', 'academic_qualification')
        }),
        ('Citizen Information', {
            'fields': ('ward', 'id_number')
        }),
        ('Terms & Timestamps', {
            'fields': ('agreed_to_Terms', 'date_joined', 'last_login')
        }),
    )

class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    raw_id_fields = ['permission']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'get_role_display', 'description')
    search_fields = ('role_name', 'description')
    inlines = [RolePermissionInline]

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission')
    search_fields = ('role__role_name', 'permission__codename')
    list_filter = ('role',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'phone_is_verified', 'website', 'created_at')
    search_fields = ('user__email', 'phone_number')
    list_filter = ('phone_is_verified', 'created_at')
    ordering = ('-created_at',)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'region', 'district', 'ward', 'created_at')
    search_fields = ('user__email', 'ward', 'office_address')
    list_filter = ('region', 'district', 'created_at')
    ordering = ('-created_at',)

@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'current_step', 'verified_by', 'verification_date', 'created_at')
    search_fields = ('user__email', 'verification_notes', 'rejection_reason')
    list_filter = ('status', 'current_step', 'verification_date', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'created_at')
    search_fields = ('user__email',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'title', 'verification_status', 'verified_by', 'is_active', 'created_at')
    search_fields = ('user__email', 'title', 'description')
    list_filter = ('document_type', 'verification_status', 'is_active', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'created_at', 'updated_at')
    search_fields = ('name', 'region__name')
    list_filter = ('region', 'created_at')
    ordering = ('region__name', 'name')

@admin.register(RegionalChapter)
class RegionalChapterAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'code', 'region__name', 'description')
    list_filter = ('is_active', 'region', 'created_at')
    ordering = ('name',)
    fieldsets = (
        ('Chapter Information', {
            'fields': ('name', 'code', 'region', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

@admin.register(OperatingRegion)
class OperatingRegionAdmin(admin.ModelAdmin):
    list_display = ('user', 'region', 'created_at')
    search_fields = ('user__email', 'region__name')
    list_filter = ('region', 'created_at')
    ordering = ('-created_at',)

@admin.register(OperatingDistrict)
class OperatingDistrictAdmin(admin.ModelAdmin):
    list_display = ('user', 'district', 'created_at')
    search_fields = ('user__email', 'district__name')
    list_filter = ('district__region', 'created_at')
    ordering = ('-created_at',)

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_sw', 'created_at', 'updated_at')
    search_fields = ('name_en', 'name_sw', 'description')
    list_filter = ('created_at', 'updated_at')
    ordering = ('name_en',)

@admin.register(ProfessionalSpecialization)
class ProfessionalSpecializationAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'years_of_experience', 'is_primary', 'created_at')
    search_fields = ('user__email', 'specialization__name_en', 'specialization__name_sw')
    list_filter = ('is_primary', 'created_at')
    ordering = ('-is_primary', '-years_of_experience')

@admin.register(AcademicRole)
class AcademicRoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_en', 'name_sw', 'created_at', 'updated_at')
    search_fields = ('code', 'name_en', 'name_sw')
    list_filter = ('created_at', 'updated_at')
    ordering = ('code',)

@admin.register(LegalSpecialization)
class LegalSpecializationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_en', 'name_sw', 'created_at', 'updated_at')
    search_fields = ('code', 'name_en', 'name_sw')
    list_filter = ('created_at', 'updated_at')
    ordering = ('code',)

@admin.register(PlaceOfWork)
class PlaceOfWorkAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_en', 'name_sw', 'created_at', 'updated_at')
    search_fields = ('code', 'name_en', 'name_sw')
    list_filter = ('created_at', 'updated_at')
    ordering = ('code',)

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'token_snippet', 'is_active', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'token', 'device_id')
    list_filter = ('device_type', 'is_active', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def token_snippet(self, obj):
        """Display first 20 characters of token for security"""
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
    token_snippet.short_description = 'Token (snippet)'

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'push_enabled', 'email_enabled', 'sms_enabled',
        'enable_reply_notifications', 'enable_like_notifications',
        'enable_comment_notifications', 'enable_message_notifications',
        'quiet_hours_enabled'
    )
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = (
        'push_enabled', 'email_enabled', 'sms_enabled',
        'enable_reply_notifications', 'enable_like_notifications',
        'enable_comment_notifications', 'enable_message_notifications',
        'quiet_hours_enabled', 'created_at'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Types', {
            'fields': (
                'enable_reply_notifications',
                'enable_like_notifications',
                'enable_comment_notifications',
                'enable_message_notifications',
                'enable_document_download_notifications'
            )
        }),
        ('Channels', {
            'fields': ('push_enabled', 'email_enabled', 'sms_enabled')
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# Device and Security Tracking Admin
@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_type', 'os_name', 'is_trusted', 'is_active', 'last_seen')
    list_filter = ('device_type', 'os_name', 'is_trusted', 'is_active', 'first_seen')
    search_fields = ('user__email', 'device_id', 'device_name', 'device_model', 'last_ip')
    readonly_fields = ('device_id', 'first_seen', 'last_seen', 'created_at', 'updated_at')
    date_hierarchy = 'last_seen'
    ordering = ('-last_seen',)
    fieldsets = (
        ('User & Device', {
            'fields': ('user', 'device_id', 'device_name', 'device_type')
        }),
        ('Operating System', {
            'fields': ('os_name', 'os_version')
        }),
        ('Browser/App', {
            'fields': ('browser_name', 'browser_version', 'app_version')
        }),
        ('Hardware', {
            'fields': ('device_model', 'device_manufacturer')
        }),
        ('Security', {
            'fields': ('is_trusted', 'is_active', 'fcm_token')
        }),
        ('Tracking', {
            'fields': ('first_seen', 'last_seen', 'last_ip')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'city', 'country', 'status', 'login_time', 'last_activity')
    list_filter = ('status', 'country', 'login_time')
    search_fields = ('user__email', 'ip_address', 'city', 'country', 'session_key')
    readonly_fields = ('session_key', 'login_time', 'last_activity', 'logout_time', 'created_at', 'updated_at')
    date_hierarchy = 'login_time'
    ordering = ('-login_time',)
    fieldsets = (
        ('User & Device', {
            'fields': ('user', 'device', 'session_key', 'status')
        }),
        ('Location', {
            'fields': ('ip_address', 'country', 'country_code', 'city', 'region', 'latitude', 'longitude', 'timezone', 'isp')
        }),
        ('Session Lifecycle', {
            'fields': ('login_time', 'last_activity', 'logout_time', 'expires_at')
        }),
        ('User Agent', {
            'fields': ('user_agent',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('email', 'status', 'ip_address', 'city', 'country', 'is_suspicious', 'timestamp')
    list_filter = ('status', 'is_suspicious', 'failure_reason', 'country', 'timestamp')
    search_fields = ('email', 'user__email', 'ip_address', 'city', 'country')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    fieldsets = (
        ('User & Status', {
            'fields': ('user', 'email', 'status', 'failure_reason')
        }),
        ('Location', {
            'fields': ('ip_address', 'country', 'city')
        }),
        ('Device Information', {
            'fields': ('device', 'user_agent', 'device_info')
        }),
        ('Security', {
            'fields': ('is_suspicious', 'suspicious_reasons')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type', 'severity', 'title', 'is_read', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_read', 'is_resolved', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'notification_sent_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        ('Alert Information', {
            'fields': ('user', 'alert_type', 'severity', 'title', 'message', 'details')
        }),
        ('Related Objects', {
            'fields': ('device', 'session')
        }),
        ('Status', {
            'fields': ('is_read', 'is_resolved', 'resolved_at')
        }),
        ('Notification', {
            'fields': ('notification_sent', 'notification_sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
