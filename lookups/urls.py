"""
Lookups URLs
URL configuration for lookup endpoints
"""

from django.urls import path
from . import views

app_name = 'lookups'

urlpatterns = [
    path('roles/', views.UserRoleListView.as_view(), name='user-roles'),
    path('regions/', views.RegionListView.as_view(), name='regions'),
    path('districts/', views.DistrictListView.as_view(), name='districts'),
    path('specializations/', views.SpecializationListView.as_view(), name='specializations'),
    path('places-of-work/', views.PlaceOfWorkListView.as_view(), name='places-of-work'),
    path('academic-roles/', views.AcademicRoleListView.as_view(), name='academic-roles'),
]
