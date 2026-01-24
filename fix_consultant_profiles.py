#!/usr/bin/env python
"""Create ConsultantProfile for legal professionals who don't have one"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from subscriptions.models import ConsultantProfile

User = get_user_model()

# Get all legal professionals without consultant profiles
legal_roles = ['advocate', 'lawyer', 'paralegal', 'law_firm']

users_without_profile = User.objects.filter(
    user_role__role_name__in=legal_roles,
    is_active=True
).exclude(
    id__in=ConsultantProfile.objects.values_list('user_id', flat=True)
)

print(f"Found {users_without_profile.count()} legal professionals without ConsultantProfile")

for user in users_without_profile:
    role = user.user_role.role_name if user.user_role else 'lawyer'
    profile = ConsultantProfile.objects.create(
        user=user,
        consultant_type=role,
        is_available=True,
        offers_physical_consultations=True,
        offers_mobile_consultations=True
    )
    print(f"  Created profile {profile.id} for user {user.id} ({user.first_name} {user.last_name})")

print("\nDone! All legal professionals now have ConsultantProfile.")
print(f"Total profiles: {ConsultantProfile.objects.count()}")
