from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserRole, Contact, Address, Verification, Document, Region, District,
    Specialization, PlaceOfWork, AcademicRole, OperatingRegion, OperatingDistrict,
    ProfessionalSpecialization
)

User = get_user_model()


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    class Meta:
        model = UserRole
        fields = ['id', 'role_name', 'get_role_display', 'description']
        read_only_fields = ['id']


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model"""
    class Meta:
        model = Region
        fields = ['id', 'name']
        read_only_fields = ['id']


class DistrictSerializer(serializers.ModelSerializer):
    """Serializer for District model"""
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'region', 'region_name']
        read_only_fields = ['id']


class SpecializationSerializer(serializers.ModelSerializer):
    """Serializer for Specialization model"""
    class Meta:
        model = Specialization
        fields = ['id', 'name_en', 'name_sw', 'description']
        read_only_fields = ['id']


class PlaceOfWorkSerializer(serializers.ModelSerializer):
    """Serializer for PlaceOfWork model"""
    class Meta:
        model = PlaceOfWork
        fields = ['id', 'code', 'name_en', 'name_sw']
        read_only_fields = ['id', 'code']


class AcademicRoleSerializer(serializers.ModelSerializer):
    """Serializer for AcademicRole model"""
    class Meta:
        model = AcademicRole
        fields = ['id', 'code', 'name_en', 'name_sw']
        read_only_fields = ['id', 'code']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact information"""
    class Meta:
        model = Contact
        fields = ['phone_number', 'phone_is_verified', 'website']


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address information"""
    region_name = serializers.CharField(source='region.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    
    class Meta:
        model = Address
        fields = ['region', 'region_name', 'district', 'district_name', 'ward', 'office_address']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles different role-specific fields dynamically.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    
    # Contact fields
    phone_number = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    
    # Address fields
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False, allow_null=True)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), required=False, allow_null=True)
    ward = serializers.CharField(required=False, allow_blank=True)
    office_address = serializers.CharField(required=False, allow_blank=True)
    
    # Operating regions and districts (for professionals)
    operating_regions = serializers.PrimaryKeyRelatedField(
        queryset=Region.objects.all(), 
        many=True, 
        required=False
    )
    operating_districts = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(), 
        many=True, 
        required=False
    )
    
    # Specializations (for legal professionals)
    specializations = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            # Basic fields
            'id', 'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'date_of_birth', 'agreed_to_Terms', 'user_role', 'gender', 'profile_picture',
            
            # Contact fields
            'phone_number', 'website',
            
            # Address fields
            'region', 'district', 'ward', 'office_address',
            
            # Professional fields (Advocate/Lawyer)
            'roll_number', 'bar_membership_number', 'practice_status', 'years_of_experience',
            'year_established', 'regional_champter', 'place_of_work', 'associated_law_firm',
            'operating_regions', 'operating_districts', 'specializations',
            
            # Law Firm fields
            'firm_name', 'managing_partner', 'number_of_lawyers',
            
            # Academic fields
            'university_name', 'academic_role', 'year_of_study', 'academic_qualification',
            
            # Citizen fields
            'id_number',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},  # Optional for law firms
            'last_name': {'required': False},   # Optional for law firms
            'date_of_birth': {'required': False},  # Optional for law firms
            'agreed_to_Terms': {'required': True},
            'user_role': {'required': True},
        }

    def validate(self, attrs):
        """Validate passwords match and role-specific requirements"""
        # Check passwords match
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        # Check terms agreement
        if not attrs.get('agreed_to_Terms'):
            raise serializers.ValidationError({"agreed_to_Terms": "You must agree to the terms and conditions."})
        
        # For law firms, make first_name, last_name, date_of_birth optional
        user_role = attrs.get('user_role')
        if user_role and user_role.role_name == 'law_firm':
            # Set default values for law firms if not provided
            if not attrs.get('first_name'):
                attrs['first_name'] = attrs.get('firm_name', 'Law Firm').split()[0]
            if not attrs.get('last_name'):
                attrs['last_name'] = 'Organization'
            if not attrs.get('date_of_birth'):
                # Use year_established or default date
                year = attrs.get('year_established', 2000)
                attrs['date_of_birth'] = f"{year}-01-01"
        
        return attrs

    def create(self, validated_data):
        """Create user with role-specific data"""
        # Remove password confirmation
        validated_data.pop('password_confirm', None)
        
        # Extract contact data
        contact_data = {
            'phone_number': validated_data.pop('phone_number', None),
            'website': validated_data.pop('website', None),
        }
        
        # Extract address data
        address_data = {
            'region': validated_data.pop('region', None),
            'district': validated_data.pop('district', None),
            'ward': validated_data.pop('ward', None),
            'office_address': validated_data.pop('office_address', None),
        }
        
        # Extract operating regions and districts
        operating_regions = validated_data.pop('operating_regions', [])
        operating_districts = validated_data.pop('operating_districts', [])
        
        # Extract specializations
        specializations = validated_data.pop('specializations', [])
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create contact if data provided
        if any(contact_data.values()):
            Contact.objects.update_or_create(
                user=user,
                defaults=contact_data
            )
        
        # Create address if data provided
        if any(address_data.values()):
            Address.objects.update_or_create(
                user=user,
                defaults=address_data
            )
        
        # Add operating regions
        for region in operating_regions:
            OperatingRegion.objects.create(user=user, region=region)
        
        # Add operating districts
        for district in operating_districts:
            OperatingDistrict.objects.create(user=user, district=district)
        
        # Add specializations
        for specialization in specializations:
            ProfessionalSpecialization.objects.create(user=user, specialization=specialization)
        
        # Auto-verify citizens and law students (no admin confirmation needed)
        user_role = user.user_role
        if user_role and user_role.role_name in ['citizen', 'law_student']:
            user.is_verified = True
            user.save()
            
            # Update verification status
            try:
                verification = user.verification
                verification.status = 'verified'
                verification.verification_date = timezone.now()
                verification.current_step = 'final'
                verification.verification_notes = 'Auto-verified upon registration (citizen/law student)'
                verification.save()
            except:
                pass
        
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for user detail view - shows only role-relevant fields"""
    user_role = UserRoleSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    address = AddressSerializer(read_only=True)
    verification_status = serializers.ReadOnlyField()
    
    # Related fields
    regional_champter = RegionSerializer(read_only=True)
    operating_regions = serializers.SerializerMethodField()
    operating_districts = serializers.SerializerMethodField()
    specializations = serializers.SerializerMethodField()
    place_of_work = PlaceOfWorkSerializer(read_only=True)
    academic_role = AcademicRoleSerializer(read_only=True)
    
    def get_operating_regions(self, obj):
        """Get regions where the professional operates"""
        return RegionSerializer(obj.regions.all(), many=True).data
    
    def get_operating_districts(self, obj):
        """Get districts where the professional operates"""
        return DistrictSerializer(obj.districts.all(), many=True).data
    
    def get_specializations(self, obj):
        """Get professional specializations"""
        return SpecializationSerializer(obj.specializations.all(), many=True).data
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'date_of_birth',
            'user_role', 'gender', 'profile_picture', 'is_active', 'is_verified',
            'contact', 'address', 'verification_status',
            
            # Professional fields
            'roll_number', 'bar_membership_number', 'practice_status',
            'years_of_experience', 'year_established', 'regional_champter',
            'place_of_work', 'associated_law_firm', 'operating_regions',
            'operating_districts', 'specializations',
            
            # Law Firm fields
            'firm_name', 'managing_partner', 'number_of_lawyers',
            
            # Academic fields
            'university_name', 'academic_role', 'year_of_study', 'academic_qualification',
            
            # Citizen fields
            'id_number',
            
            'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_verified']
    
    def to_representation(self, instance):
        """Filter fields based on user role - only show relevant fields"""
        data = super().to_representation(instance)
        
        if not instance.user_role:
            return data
        
        role_name = instance.user_role.role_name
        
        # Define fields for each role
        role_fields = {
            'citizen': [
                'id', 'email', 'first_name', 'last_name', 'date_of_birth',
                'user_role', 'gender', 'profile_picture', 'is_active', 'is_verified',
                'contact', 'address', 'verification_status', 'id_number',
                'date_joined', 'last_login'
            ],
            'advocate': [
                'id', 'email', 'first_name', 'last_name', 'date_of_birth',
                'user_role', 'gender', 'profile_picture', 'is_active', 'is_verified',
                'contact', 'address', 'verification_status',
                'roll_number', 'practice_status', 'year_established', 'regional_champter',
                'operating_regions', 'specializations', 'associated_law_firm',
                'date_joined', 'last_login'
            ],
            'lawyer': [
                'id', 'email', 'first_name', 'last_name', 'date_of_birth',
                'user_role', 'gender', 'profile_picture', 'is_active', 'is_verified',
                'contact', 'address', 'verification_status',
                'bar_membership_number', 'years_of_experience', 'place_of_work',
                'operating_regions', 'operating_districts', 'specializations',
                'associated_law_firm', 'date_joined', 'last_login'
            ],
            'paralegal': [
                'id', 'email', 'first_name', 'last_name', 'date_of_birth',
                'user_role', 'gender', 'profile_picture', 'is_active', 'is_verified',
                'contact', 'address', 'verification_status',
                'years_of_experience', 'place_of_work', 'operating_regions',
                'operating_districts', 'associated_law_firm',
                'date_joined', 'last_login'
            ],
            'law_firm': [
                'id', 'email', 'user_role', 'profile_picture', 'is_active', 'is_verified',
                'contact', 'address', 'verification_status',
                'firm_name', 'managing_partner', 'number_of_lawyers', 'year_established',
                'specializations', 'date_joined', 'last_login'
            ],
            'law_student': [
                'id', 'email', 'first_name', 'last_name', 'date_of_birth',
                'user_role', 'gender', 'profile_picture', 'is_active', 'is_verified',
                'contact', 'verification_status',
                'university_name', 'academic_role', 'year_of_study', 'academic_qualification',
                'date_joined', 'last_login'
            ]
        }
        
        # Get allowed fields for this role
        allowed_fields = role_fields.get(role_name, data.keys())
        
        # Filter data to only include allowed fields
        filtered_data = {key: value for key, value in data.items() if key in allowed_fields}
        
        # Remove null values and empty arrays/objects
        cleaned_data = {}
        for key, value in filtered_data.items():
            # Keep these fields even if null/empty
            if key in ['id', 'email', 'user_role', 'is_active', 'is_verified', 
                      'verification_status', 'date_joined', 'last_login']:
                cleaned_data[key] = value
            # Remove null values
            elif value is None:
                continue
            # Remove empty lists
            elif isinstance(value, list) and len(value) == 0:
                continue
            # Keep everything else
            else:
                cleaned_data[key] = value
        
        return cleaned_data
