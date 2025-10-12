from django.contrib import admin
from .models import (
    AcademicRole, LegalSpecialization, PlaceOfWork, UserRole, RolePermission,
    Contact, Address, Verification, VerificationDocument, Document, PolaUser,
    Region, District, OperatingRegion, OperatingDistrict, Specialization,
    ProfessionalSpecialization
)

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
                      'year_established', 'regional_champter', 'place_of_work', 'associated_law_firm')
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
    readonly_fields = ('code',)

@admin.register(LegalSpecialization)
class LegalSpecializationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_en', 'name_sw', 'created_at', 'updated_at')
    search_fields = ('code', 'name_en', 'name_sw')
    list_filter = ('created_at', 'updated_at')
    ordering = ('code',)
    readonly_fields = ('code',)

@admin.register(PlaceOfWork)
class PlaceOfWorkAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_en', 'name_sw', 'created_at', 'updated_at')
    search_fields = ('code', 'name_en', 'name_sw')
    list_filter = ('created_at', 'updated_at')
    ordering = ('code',)
    readonly_fields = ('code',)
