from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from subscriptions.models import ConsultantProfile


class Command(BaseCommand):
    help = 'Create ConsultantProfile for legal professionals who do not have one'

    def handle(self, *args, **options):
        User = get_user_model()
        
        legal_roles = ['advocate', 'lawyer', 'paralegal', 'law_firm']
        
        # Get all legal professionals without consultant profiles
        users_without_profile = User.objects.filter(
            user_role__role_name__in=legal_roles,
            is_active=True
        ).exclude(
            id__in=ConsultantProfile.objects.values_list('user_id', flat=True)
        )
        
        count = users_without_profile.count()
        self.stdout.write(f"Found {count} legal professionals without ConsultantProfile")
        
        for user in users_without_profile:
            role = user.user_role.role_name if user.user_role else 'lawyer'
            years_exp = user.years_of_experience if hasattr(user, 'years_of_experience') and user.years_of_experience else 0
            profile = ConsultantProfile.objects.create(
                user=user,
                consultant_type=role,
                is_available=True,
                offers_physical_consultations=True,
                offers_mobile_consultations=True,
                years_of_experience=years_exp
            )
            self.stdout.write(f"  Created profile {profile.id} for user {user.id} ({user.first_name} {user.last_name})")
        
        self.stdout.write(self.style.SUCCESS(f"Done! Total profiles: {ConsultantProfile.objects.count()}"))
