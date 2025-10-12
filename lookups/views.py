"""
Lookups Views
Provides lookup/reference data for dropdowns and selections
"""

from rest_framework import generics, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from authentication.models import (
    UserRole, Region, District, Specialization, 
    PlaceOfWork, AcademicRole
)
from .serializers import (
    UserRoleSerializer,
    RegionSerializer,
    DistrictSerializer,
    SpecializationSerializer,
    PlaceOfWorkSerializer,
    AcademicRoleSerializer,
)


class UserRoleListView(generics.ListAPIView):
    """List all available user roles"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all user roles",
        tags=['Lookups']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RegionListView(generics.ListAPIView):
    """List all regions"""
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all regions in Tanzania",
        tags=['Lookups']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DistrictListView(generics.ListAPIView):
    """List all districts, optionally filtered by region"""
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = District.objects.all()
        region_id = self.request.query_params.get('region', None)
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        return queryset
    
    @swagger_auto_schema(
        operation_description="Get list of all districts, optionally filtered by region",
        manual_parameters=[
            openapi.Parameter(
                'region',
                openapi.IN_QUERY,
                description="Filter districts by region ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        tags=['Lookups']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SpecializationListView(generics.ListAPIView):
    """List all legal specializations"""
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all legal specializations/practice areas",
        tags=['Lookups']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PlaceOfWorkListView(generics.ListAPIView):
    """List all place of work options"""
    queryset = PlaceOfWork.objects.all()
    serializer_class = PlaceOfWorkSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all place of work options",
        tags=['Lookups']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AcademicRoleListView(generics.ListAPIView):
    """List all academic roles"""
    queryset = AcademicRole.objects.all()
    serializer_class = AcademicRoleSerializer
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of all academic roles (student, lecturer, etc.)",
        tags=['Lookups']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
