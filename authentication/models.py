# users/models.py
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from .choices import *


from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames. The manager class defines
    the create_user and create_superuser methods.
    """

    def create_user(
        self,
        email,
        password=None,
        date_of_birth=None,
        agreed_to_Terms=None,
        phone_number=None,  # We'll use this for Contact creation
        **extra_fields
    ):
        """
        Create and save a regular user with the given email, date of birth, and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            date_of_birth=date_of_birth,
            agreed_to_Terms=agreed_to_Terms,
            **extra_fields
        )
        user.set_password(password)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_superuser", False)
        user.save(using=self._db)
        
        # Create contact information if phone number is provided
        if phone_number:
            Contact.objects.create(
                user=user,
                phone_number=phone_number,
                phone_is_verified=False
            )
        
        # Create verification status for new user
        Verification.objects.create(user=user)
            
        return user

    def create_superuser(
        self,
        email,
        password=None,
        date_of_birth=None,
        agreed_to_Terms=True,  # Superusers automatically agree to terms
        phone_number=None,
        **extra_fields
    ):
        """
        Create and save a superuser with the given email, date of birth, and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            email=email,
            password=password,
            date_of_birth=date_of_birth,
            agreed_to_Terms=agreed_to_Terms,
            phone_number=phone_number,
            **extra_fields
        )
    
class UserRole(models.Model):
    ROLE_CHOICES = [
        ('lawyer', {'en': 'Lawyer', 'sw': 'Mwanasheria'}),
        ('advocate', {'en': 'Advocate', 'sw': 'Wakili'}),
        ('paralegal', {'en': 'Paralegal', 'sw': 'Msaidizi wa Kisheria'}),
        ('law_student', {'en': 'Law Student', 'sw': 'Mwanafunzi wa Sheria/Mhadhiri'}),
        ('law_firm', {'en': 'Law Firm', 'sw': 'Ofisi ya Mawakili'}),
        ('citizen', {'en': 'Citizen', 'sw': 'Mwananchi'}),
    ]
    
    role_name = models.CharField(max_length=255, unique=True, choices=[(code, data['en']) for code, data in ROLE_CHOICES])
    
    def get_role_display_sw(self):
        """Get the Swahili display name for the role"""
        for code, data in self.ROLE_CHOICES:
            if code == self.role_name:
                return data['sw']
        return ''

    def get_role_display_en(self):
        """Get the English display name for the role"""
        for code, data in self.ROLE_CHOICES:
            if code == self.role_name:
                return data['en']
        return ''

    def get_role_display(self):
        """Override the default get_role_name_display to support both languages"""
        return f"{self.get_role_display_en()} / {self.get_role_display_sw()}"
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name=_('permissions'),
    )

    def __str__(self):
        return self.get_role_display()
    
    def assign_permission(self, permission_codename):
        """Assign a permission to this role."""
        try:
            permission = Permission.objects.get(codename=permission_codename)
            RolePermission.objects.get_or_create(role=self, permission=permission)
            return True
        except Permission.DoesNotExist:
            return False
    
    def remove_permission(self, permission_codename):
        """Remove a permission from this role."""
        try:
            permission = Permission.objects.get(codename=permission_codename)
            RolePermission.objects.filter(role=self, permission=permission).delete()
            return True
        except Permission.DoesNotExist:
            return False
    
    def has_permission(self, permission_codename):
        """Check if this role has a specific permission."""
        return self.permissions.filter(codename=permission_codename).exists()

    @classmethod
    def get_roles_by_language(cls, language='en'):
        """
        Get all roles in the specified language
        Args:
            language (str): 'en' for English or 'sw' for Swahili
        Returns:
            list: List of tuples (role_code, role_name) in the specified language
        """
        return [(code, data[language]) for code, data in cls.ROLE_CHOICES]

class RolePermission(models.Model):
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = _('role permission')
        verbose_name_plural = _('role permissions')

    def __str__(self):
        return f"{self.role.get_role_name_display()} - {self.permission.codename}"

class Contact(models.Model):
    """Model for storing contact information"""
    user = models.OneToOneField('PolaUser', on_delete=models.CASCADE, related_name='contact')
    phone_number = models.CharField(max_length=15, verbose_name=_("Phone Number"), null=True)
    phone_is_verified = models.BooleanField(default=False)
    website = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contact info for {self.user}"

    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")

class Address(models.Model):
    """Model for storing address information"""
    user = models.OneToOneField('PolaUser', on_delete=models.CASCADE, related_name='address')
    region = models.ForeignKey('Region', on_delete=models.SET_NULL, null=True, related_name='addresses')
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, related_name='addresses')
    ward = models.CharField(max_length=100, null=True)
    office_address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Address for {self.user}"

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

class Verification(models.Model):
    """Model for managing user verification status
    advocate
    - verification iss made by admins
    
    """
    VERIFICATION_STATUS = [
        ('pending', _('Pending Verification')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
    ]

    VERIFICATION_STEP = [
        ('documents', _('Document Verification')),
        ('identity', _('Identity Verification')),
        ('contact', _('Contact Information')),
        ('role_specific', _('Role-Specific Requirements')),
        ('final', _('Final Approval')),
    ]

    user = models.OneToOneField('PolaUser', on_delete=models.CASCADE, related_name='verification')
    status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending',
        help_text=_("Overall verification status of the user")
    )
    current_step = models.CharField(
        max_length=20,
        choices=VERIFICATION_STEP,
        default='documents',
        help_text=_("Current verification step")
    )
    verified_by = models.ForeignKey(
        'PolaUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users'
    )
    verification_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Verification status for {self.user}: {self.get_status_display()}"

    class Meta:
        verbose_name = _("verification")
        verbose_name_plural = _("verifications")

    def verify_step(self, step, verified_by, notes=None):
        """Verify a specific step of the verification process"""
        if step == self.current_step:
            steps = [choice[0] for choice in self.VERIFICATION_STEP]
            current_index = steps.index(step)
            
            if current_index + 1 < len(steps):
                self.current_step = steps[current_index + 1]
            else:
                self.status = 'verified'
                self.verification_date = timezone.now()
                self.verified_by = verified_by
            
            if notes:
                self.verification_notes = (self.verification_notes or '') + f"\n{step}: {notes}"
            self.save()
            return True
        return False

    def reject(self, verified_by, reason):
        """Reject the verification"""
        self.status = 'rejected'
        self.verified_by = verified_by
        self.rejection_reason = reason
        self.verification_date = timezone.now()
        self.save()

    @property
    def is_verified(self):
        """Check if the user is fully verified"""
        return self.status == 'verified'

    @property
    def verification_progress(self):
        """Get verification progress as a percentage"""
        steps = [choice[0] for choice in self.VERIFICATION_STEP]
        current_index = steps.index(self.current_step)
        return ((current_index + 1) / len(steps)) * 100



class VerificationDocument(models.Model):
    """Model for storing verification documents"""
    user = models.ForeignKey('PolaUser', on_delete=models.CASCADE, related_name='verification_documents')
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='verification_documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Verification Document for {self.user}"

class Document(models.Model):
    """Model for storing and verifying user documents"""
    DOCUMENT_TYPES = [
        # Advocate documents
        ('roll_number_cert', _('Roll Number Certificate')),
        ('practice_license', _('Practice License')),
        ('work_certificate', _('Certificate of Work')),
        
        # Lawyer/Paralegal documents
        ('professional_cert', _('Professional Certificate')),
        ('employment_letter', _('Employment Letter')),
        ('organization_cert', _('Organization Certificate')),
        
        # Law Firm documents
        ('business_license', _('Business License')),
        ('registration_cert', _('Registration Certificate')),
        ('firm_documents', _('Other Firm Documents')),
        
        # General
        ('id_document', _('ID Document')),
        ('academic', _('Academic Certificate')),
        ('other', _('Other Document')),
    ]

    VERIFICATION_STATUS = [
        ('pending', _('Pending Verification')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
    ]

    user = models.ForeignKey('PolaUser', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='user_documents/')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    verified_by = models.ForeignKey(
        'PolaUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.user}"

    class Meta:
        verbose_name = _("document")
        verbose_name_plural = _("documents")
        ordering = ['-created_at']

    def verify(self, verified_by, status='verified', notes=None):
        """Verify the document"""
        self.verification_status = status
        self.verified_by = verified_by
        self.verification_date = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save()

    @property
    def is_verified(self):
        """Check if the document is verified"""
        return self.verification_status == 'verified'



class PolaUser(AbstractUser):

    """
    Custom user model to support multiple roles with specific fields. Each role has its own set of required fields.
     advocate
     1. roll_number
     2. gender
     3. regional_chamber(list of regions)
     4. year of admission
     5. practice_status (active/inactive)
     6. law_firm (name of the law firm)
     7. specialization/Practice Area (list of legal fields)
     7. contact_information (phone number, email)
     8. office_address (physical address of the office)
     9. gender

     lawyer/paralegal
     place_of_work (where they work: Law Firm, Legal Aid Organization, Government Agency, Private Company, NGO etc.)
     years_of_experience
     gender
     region_of_operation (list of regions)
     district_of_operation (list of districts)
     contact_information (phone number, email)    
     office_address (physical address of the office)
     bar_membership_number (if applicable)  

    law Firm
    name of the firm   
    registration_certificate(upload document) 
    Managing Partner/Principal advocate (name of the managing partner)
    number_of_lawyers/advocates (number of lawyers in the firm)
    year_established (year the firm was established)
    office_address (physical address of the firm)
    offic_address (physical address of the office)
    contact_information (phone number, email, website)
    areas_of_specialization/Practice area (list of legal fields the firm specializes in) 
    profile_photo (upload image)


    law student or lecturer
    university_name (name of the university)
    type (student or lecturer)
    gender (male, female, other)
    contact_information (phone number, email)
    year_of_study (for students)

    citizen
    gender
    1. location (region, district, ward)
    2. id_number
    3. profile_picture
    4. contact_information (phone number, email)
    5. region
    6. district  

    """
  
    username = None
    date_of_birth = models.DateField(verbose_name="Birthday", null=True)
    agreed_to_Terms = models.BooleanField(default=False)
    user_role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Common fields for all users
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)
    
    # Keep email in PolaUser as it's the login field
    email = models.EmailField(_("email address"), unique=True)
    
    # Common fields for Legal Professionals (Advocate, Lawyer, Law Firm)
    # same as area of work
    specializations = models.ManyToManyField(
        'Specialization',
        through='ProfessionalSpecialization',
        related_name='users',
        verbose_name=_("Practice Areas/Specializations"),
        help_text=_("Legal fields of expertise or areas of specialization")
    )
    practice_status = models.CharField(
        max_length=20, 
        choices=PRACTICE_STATUS_CHOICES, 
        null=True,
        help_text=_("Current practice status (active/inactive)")
    )
    year_established = models.IntegerField(
        null=True, 
        help_text=_("Year of establishment (for firms) or year of admission to practice (for advocates/lawyers)")
    )
    
    @property
    def registration_certificate(self):
        """Get the user's verified registration certificate"""
        return self.documents.filter(
            document_type='registration',
            verification_status='verified',
            is_active=True
        ).first()
    
    # Fields specific to Individual Legal Professionals (Advocate/Lawyer/Paralegal)
    roll_number = models.CharField(max_length=50, unique=True, null=True)  # For advocates
    bar_membership_number = models.CharField(max_length=50, null=True, blank=True)  # For lawyers
    years_of_experience = models.PositiveIntegerField(null=True)
    
    # Operation Areas (where the professional practices)
    regions = models.ManyToManyField(
        'Region',
        through='OperatingRegion',
        related_name='professionals',
        verbose_name=_("Regional Chambers/Regions of Operation"),
        help_text=_("Regions where the professional operates/practices or has registered chambers")
    )
    districts = models.ManyToManyField(
        'District',
        through='OperatingDistrict',
        related_name='professionals',
        verbose_name=_("Districts of Operation"),
        help_text=_("Districts where the professional operates/practices")
    )
    # same as regions
    regional_champter = models.ForeignKey('Region', on_delete=models.SET_NULL, null=True, related_name='chamber_professionals')
    place_of_work = models.ForeignKey('PlaceOfWork', on_delete=models.SET_NULL, null=True, related_name='professionals')
    associated_law_firm = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        limit_choices_to={'user_role__role_name': 'law_firm'},
        related_name='associated_professionals'
    )
    
    # Fields specific to Law Firm
    firm_name = models.CharField(max_length=255, null=True)
    managing_partner = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        limit_choices_to={'user_role__role_name': 'advocate'},
        related_name='managing_firms'
    )
    number_of_lawyers = models.PositiveIntegerField(null=True)
    
    # Fields for Academic (Students/Lecturers)
    university_name = models.CharField(max_length=255, null=True)
    academic_role = models.ForeignKey('AcademicRole', on_delete=models.SET_NULL, null=True, related_name='users')
    year_of_study = models.PositiveIntegerField(null=True, blank=True)  # Only for students
    academic_qualification = models.CharField(max_length=255, null=True, blank=True)  # For lecturers/professors
    
    # Fields for Citizen
    ward = models.CharField(max_length=100, null=True)
    id_number = models.CharField(max_length=50, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="customuser_set",  # Changed related_name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="customuser_set",  # Changed related_name
        related_query_name="customuser",
    )
    last_login = models.DateTimeField(
        _("last login"), auto_now=False, null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "date_of_birth",
        "agreed_to_Terms",
    ]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        if self.email is not None:
            return self.email
        return self.phone_number
        
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.user_role and self.user_role.role_name == role_name
    
    def has_permission(self, permission_codename):
        """
        Check if user has a specific permission through their role
        or direct user permissions.
        """
        # Check direct user permissions first
        if self.has_perm(permission_codename):
            return True
            
        # Check role-based permissions
        return (
            self.user_role and 
            self.user_role.has_permission(permission_codename)
        )
    
    def assign_role(self, role_name):
        """Assign a role to the user."""
        try:
            role = UserRole.objects.get(role_name=role_name)
            self.user_role = role
            self.save()
            
            # Create or update verification status when role is assigned
            Verification.objects.get_or_create(user=self)
            return True
        except UserRole.DoesNotExist:
            return False
            
    @property
    def is_verified(self):
        """Check if the user is fully verified"""
        return hasattr(self, 'verification') and self.verification.is_verified
    
    @property
    def verification_status(self):
        """Get the user's verification status"""
        if hasattr(self, 'verification'):
            return {
                'status': self.verification.get_status_display(),
                'current_step': self.verification.get_current_step_display(),
                'progress': self.verification.verification_progress,
                'notes': self.verification.verification_notes,
                'verification_date': self.verification.verification_date
            }
        return None
        
    def full_name (self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def initialize_role_data(self, data):
        """Initialize role-specific data when assigning a role."""
        if not self.user_role:
            raise ValueError("User must have a role before initializing role data")
            
        # Create or update contact info
        contact_data = {
            'phone_number': data.pop('phone_number', None),
            'phone_is_verified': data.pop('phone_is_verified', False),
            'website': data.pop('website', None)
        }
        if any(v is not None for v in contact_data.values()):
            Contact.objects.update_or_create(user=self, defaults=contact_data)
            
        # Create or update address info
        address_data = {
            'ward': data.pop('ward', None),
            'office_address': data.pop('office_address', None)
        }
        
        # Handle region and district
        region_name = data.pop('region', None)
        district_name = data.pop('district', None)
        
        if region_name:
            region = Region.objects.get(name=region_name)
            address_data['region'] = region
            
            if district_name:
                district = District.objects.get(name=district_name, region=region)
                address_data['district'] = district
                
        if any(v is not None for v in address_data.values()):
            Address.objects.update_or_create(user=self, defaults=address_data)
            
        # Handle operating regions and districts
        operating_regions = data.pop('regions_of_operation', [])
        operating_districts = data.pop('districts_of_operation', [])
        
        if operating_regions:
            # Clear existing operating regions first
            self.operating_regions.all().delete()
            # Add new operating regions
            for region_name in operating_regions:
                region = Region.objects.get(name=region_name)
                OperatingRegion.objects.create(user=self, region=region)
                
        if operating_districts:
            # Clear existing operating districts first
            self.operating_districts.all().delete()
            # Add new operating districts
            for district_name in operating_districts:
                district = District.objects.filter(name=district_name).first()
                if district:
                    OperatingDistrict.objects.create(user=self, district=district)
            
        # Handle documents
        registration_cert = data.pop('registration_certificate', None)
        if registration_cert:
            Document.objects.create(
                user=self,
                document_type='registration',
                file=registration_cert,
                title=f"Registration Certificate for {self.get_full_name()}",
                description=f"Registration certificate for {self.user_role.get_role_display()}"
            )
            
        # Update remaining fields in user model
        allowed_fields = set(self.get_role_fields())
        for field, value in data.items():
            if field in allowed_fields:
                setattr(self, field, value)
        self.full_clean()
        self.save()
    
    def get_role_fields(self):
        """Get the fields relevant to the user's role."""
        # Common fields for all users - these are in the base user model
        all_common_fields = ['gender', 'profile_picture', 'email']
        
        # Fields for legal professionals
        legal_professional_fields = [
            'specialization', 'practice_status', 'registration_certificate',
            'year_established', 'website'
        ]
        
        role_fields = {
            'advocate': [
                *all_common_fields,
                *legal_professional_fields,
                'roll_number',
                'regional_champter',
                'regions_of_operation',
                'districts_of_operation',
                'years_of_experience',
                'associated_law_firm'
            ],
            'lawyer': [
                *all_common_fields,
                *legal_professional_fields,
                'bar_membership_number',
                'place_of_work',
                'years_of_experience',
                'regions_of_operation',
                'districts_of_operation',
                'associated_law_firm'
            ],
            'paralegal': [
                *all_common_fields,
                'place_of_work',
                'years_of_experience',
                'regions_of_operation',
                'districts_of_operation',
                'associated_law_firm'
            ],
            'law_firm': [
                *all_common_fields,
                *legal_professional_fields,
                'firm_name',
                'managing_partner',
                'number_of_lawyers'
            ],
            'law_student': [
                *all_common_fields,
                'university_name',
                'academic_role',
                'year_of_study'
            ],
            'lecturer': [
                *all_common_fields,
                'university_name',
                'academic_role',
                'academic_qualification'
            ],
            'citizen': [
                *all_common_fields,
                'id_number'
            ]
        }
        
        if not self.user_role:
            return []
            
        return role_fields.get(self.user_role.role_name, [])
    
    def clean(self):
        """Validate role-specific fields."""
        super().clean()
        if self.user_role:
            required_fields = self.get_role_fields()
            for field in required_fields:
                if getattr(self, field, None) is None:
                    raise ValidationError({field: f"{field} is required for {self.user_role.get_role_display()}"})
    
    def get_role_data(self):
        """Get all role-specific data as a dictionary."""
        if not self.user_role:
            return {}
            
        return {
            field: getattr(self, field)
            for field in self.get_role_fields()
            if getattr(self, field) is not None
        }
    
    def update_role_data(self, data):
        """Update role-specific fields."""
        if not self.user_role:
            raise ValueError("User must have a role before updating role data")
            
        # Update contact info
        if hasattr(self, 'contact'):
            contact_data = {
                'phone_number': data.pop('phone_number', self.contact.phone_number),
                'phone_is_verified': data.pop('phone_is_verified', self.contact.phone_is_verified),
                'website': data.pop('website', self.contact.website)
            }
            for field, value in contact_data.items():
                if value is not None:
                    setattr(self.contact, field, value)
            self.contact.save()
            
        # Update address info
        if hasattr(self, 'address'):
            address_data = {
                'region': data.pop('region', self.address.region),
                'district': data.pop('district', self.address.district),
                'ward': data.pop('ward', self.address.ward),
                'office_address': data.pop('office_address', self.address.office_address)
            }
            for field, value in address_data.items():
                if value is not None:
                    setattr(self.address, field, value)
            self.address.save()
            
        # Update remaining fields in user model
        allowed_fields = set(self.get_role_fields())
        for field, value in data.items():
            if field in allowed_fields:
                setattr(self, field, value)
        self.full_clean()
        self.save()

class Region(models.Model):
    """Model for storing regions in Tanzania"""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("region")
        verbose_name_plural = _("regions")
        ordering = ['name']


class District(models.Model):
    """Model for storing districts in Tanzania"""
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.region.name}"

    class Meta:
        verbose_name = _("district")
        verbose_name_plural = _("districts")
        ordering = ['region__name', 'name']
        unique_together = ['name', 'region']  # A district name should be unique within a region

class OperatingRegion(models.Model):
    """Model for storing regions where a professional operates"""
    user = models.ForeignKey('PolaUser', on_delete=models.CASCADE, related_name='operating_regions')
    region = models.ForeignKey('Region', on_delete=models.CASCADE, related_name='operating_professionals')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("operating region")
        verbose_name_plural = _("operating regions")
        unique_together = ['user', 'region']  # A user can't have the same region twice

    def __str__(self):
        return f"{self.user} - {self.region}"


class OperatingDistrict(models.Model):
    """Model for storing districts where a professional operates"""
    user = models.ForeignKey('PolaUser', on_delete=models.CASCADE, related_name='operating_districts')
    district = models.ForeignKey('District', on_delete=models.CASCADE, related_name='operating_professionals')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("operating district")
        verbose_name_plural = _("operating districts")
        unique_together = ['user', 'district']  # A user can't have the same district twice

    def __str__(self):
        return f"{self.user} - {self.district}"

class Specialization(models.Model):
    """Model for storing legal practice areas and specializations"""
    name_en = models.CharField(
        max_length=255,
        verbose_name=_("Name (English)"),
        help_text=_("Practice area name in English")
    )
    name_sw = models.CharField(
        max_length=255,
        verbose_name=_("Name (Swahili)"),
        help_text=_("Practice area name in Swahili")
    )
    description = models.TextField(
        null=True, 
        blank=True,
        help_text=_("Description of this practice area")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("specialization")
        verbose_name_plural = _("specializations")
        ordering = ['name_en']

    def __str__(self):
        return f"{self.name_en} / {self.name_sw}"

    @property
    def name(self):
        """Get name in both languages"""
        return {
            'en': self.name_en,
            'sw': self.name_sw
        }

class ProfessionalSpecialization(models.Model):
    """Model for linking professionals to their specializations"""
    user = models.ForeignKey('PolaUser', on_delete=models.CASCADE, related_name='professional_specializations')
    specialization = models.ForeignKey('Specialization', on_delete=models.CASCADE, related_name='professionals')
    years_of_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Years of experience in this specific practice area")
    )
    is_primary = models.BooleanField(
        default=False,
        help_text=_("Whether this is one of the professional's primary practice areas")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("professional specialization")
        verbose_name_plural = _("professional specializations")
        unique_together = ['user', 'specialization']  # A user can't have the same specialization twice
        ordering = ['-is_primary', '-years_of_experience']

    def __str__(self):
        return f"{self.user} - {self.specialization}"

    @property
    def regional_chamber(self):
        """Get the regional chamber for an advocate"""
        if not self.has_role('advocate'):
            return None
        # Get the first operating region as the chamber
        operating_region = self.operating_regions.first()
        return operating_region.region if operating_region else None

    def set_regional_chamber(self, region):
        """Set the regional chamber for an advocate"""
        if not self.has_role('advocate'):
            raise ValueError("Only advocates can have a regional chamber")
        
        if isinstance(region, str):
            region = Region.objects.get(name=region)
            
        # Clear existing operating regions
        self.operating_regions.all().delete()
        # Create new operating region as chamber
        if region:
            OperatingRegion.objects.create(user=self, region=region)

    @staticmethod
    def get_advocates_by_chamber(chamber):
        """Get all advocates in a specific chamber"""
        return PolaUser.objects.filter(
            user_role__role_name='advocate',
            operating_regions__region=chamber
        )

class LegalSpecialization(models.Model):
    """Model for storing legal specialization choices"""
    code = models.CharField(max_length=50, unique=True, blank=True)
    name_en = models.CharField(max_length=255)
    name_sw = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("legal specialization")
        verbose_name_plural = _("legal specializations")
        ordering = ['name_en']

    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code from name_en: convert to lowercase, replace spaces with underscores
            self.code = self.name_en.lower().replace(' ', '_').replace('/', '_').replace('-', '_')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name_en} / {self.name_sw}"

    @property
    def name(self):
        """Get name in both languages"""
        return {
            'en': self.name_en,
            'sw': self.name_sw
        }

class PlaceOfWork(models.Model):
    """Model for storing place of work choices"""
    code = models.CharField(max_length=50, unique=True, blank=True)
    name_en = models.CharField(max_length=255)
    name_sw = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("place of work")
        verbose_name_plural = _("places of work")
        ordering = ['name_en']

    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code from name_en: convert to lowercase, replace spaces with underscores
            self.code = self.name_en.lower().replace(' ', '_').replace('/', '_').replace('-', '_').replace('(', '').replace(')', '')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name_en} / {self.name_sw}"

    @property
    def name(self):
        """Get name in both languages"""
        return {
            'en': self.name_en,
            'sw': self.name_sw
        }

class AcademicRole(models.Model):
    """Model for storing academic role choices with bilingual support"""
    code = models.CharField(max_length=50, unique=True, blank=True)
    name_en = models.CharField(max_length=255)
    name_sw = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("academic role")
        verbose_name_plural = _("academic roles")
        ordering = ['name_en']

    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code from name_en: convert to lowercase, replace spaces with underscores
            self.code = self.name_en.lower().replace(' ', '_').replace('/', '_').replace('-', '_')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name_en} / {self.name_sw}"

    @property
    def name(self):
        """Get name in both languages"""
        return {
            'en': self.name_en,
            'sw': self.name_sw
        }

