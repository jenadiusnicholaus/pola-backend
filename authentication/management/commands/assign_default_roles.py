"""
Management command to assign default roles to users who don't have one
Run: python manage.py assign_default_roles
"""

from django.core.management.base import BaseCommand
from authentication.models import PolaUser, UserRole


class Command(BaseCommand):
    help = 'Assigns default roles to users without a role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-role',
            type=str,
            default='citizen',
            help='Default role to assign to users without a role (default: citizen)'
        )
        parser.add_argument(
            '--skip-staff',
            action='store_true',
            help='Skip staff and superuser accounts'
        )

    def handle(self, *args, **options):
        default_role_name = options['default_role']
        skip_staff = options['skip_staff']
        
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("  🔧 Assigning Default Roles to Users"))
        self.stdout.write("=" * 70)
        
        # Get the default role
        try:
            default_role = UserRole.objects.get(role_name=default_role_name)
            self.stdout.write(f"\n✓ Default role: {default_role.get_role_display()}")
        except UserRole.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"\n✗ Role '{default_role_name}' does not exist!")
            )
            self.stdout.write("Available roles:")
            for role in UserRole.objects.all():
                self.stdout.write(f"  - {role.role_name}")
            return
        
        # Find users without roles
        users_without_role = PolaUser.objects.filter(user_role__isnull=True)
        
        if skip_staff:
            users_without_role = users_without_role.filter(is_staff=False, is_superuser=False)
        
        count = users_without_role.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("\n✓ All users already have roles assigned!"))
            return
        
        self.stdout.write(f"\nFound {count} user(s) without a role:\n")
        
        # Assign default role
        assigned_count = 0
        for user in users_without_role:
            user_type = ""
            if user.is_superuser:
                user_type = " [SUPERUSER]"
            elif user.is_staff:
                user_type = " [STAFF]"
            
            self.stdout.write(f"  • {user.email}{user_type}")
            user.user_role = default_role
            user.save()
            assigned_count += 1
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"  ✅ Assigned '{default_role_name}' role to {assigned_count} user(s)"))
        self.stdout.write("=" * 70)
        
        # Suggest running seed_permissions
        self.stdout.write("\n" + self.style.WARNING("💡 TIP: Run 'python manage.py seed_permissions' to ensure permissions are up to date"))
