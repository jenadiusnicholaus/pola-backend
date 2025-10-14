"""
Lookups Serializers
Serializers for lookup/reference data
"""

from rest_framework import serializers
from authentication.models import (
    UserRole, Region, District, Specialization,
    PlaceOfWork, AcademicRole
)


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    class Meta:
        model = UserRole
        fields = ['id', 'role_name', 'get_role_display', 'description']
        ref_name = 'LookupUserRole'


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model"""
    class Meta:
        model = Region
        fields = ['id', 'name']
        ref_name = 'LookupRegion'


class DistrictSerializer(serializers.ModelSerializer):
    """Serializer for District model"""
    region_name = serializers.CharField(source='region.name', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'region', 'region_name']
        ref_name = 'LookupDistrict'


class SpecializationSerializer(serializers.ModelSerializer):
    """Serializer for Specialization model"""
    class Meta:
        model = Specialization
        fields = ['id', 'name_en', 'name_sw', 'description']
        ref_name = 'LookupSpecialization'


class PlaceOfWorkSerializer(serializers.ModelSerializer):
    """Serializer for PlaceOfWork model"""
    class Meta:
        model = PlaceOfWork
        fields = ['id', 'code', 'name_en', 'name_sw']
        ref_name = 'LookupPlaceOfWork'


class AcademicRoleSerializer(serializers.ModelSerializer):
    """Serializer for AcademicRole model"""
    class Meta:
        model = AcademicRole
        fields = ['id', 'code', 'name_en', 'name_sw']
        ref_name = 'LookupAcademicRole'
