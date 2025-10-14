"""
Management command to seed role-based permissions using Django's model permissions
Run: python manage.py seed_permissions

This uses Django's built-in model permissions:
- add_<model>
- change_<model>
- delete_<model>
- view_<model>
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from authentication.models import UserRole, PolaUser, Document, Verification, Contact, Address


class Command(BaseCommand):
    help = 'Seeds role-based permissions using Django model permissions'

    def handle(self, *args, **kwargs):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("  🔐 Seeding Role-Based Permissions (Model-Based)"))
        self.stdout.write("=" * 70)
        
        # Django automatically creates these permissions for each model:
        # - add_<modelname>
        # - change_<modelname>
        # - delete_<modelname>
        # - view_<modelname>
        
        self.stdout.write("\n📋 Available Model Permissions:")
        self.stdout.write("-" * 70)
        
        models = [PolaUser, Document, Verification, Contact, Address]
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=content_type)
            self.stdout.write(f"\n{model.__name__}:")
            for perm in perms:
                self.stdout.write(f"  • {perm.codename} - {perm.name}")
        
        # Define additional custom permissions if needed (beyond model permissions)
        custom_permissions_data = [
            {
                'codename': 'can_verify_others',
                'name': 'Can verify other users',
                'model': PolaUser
            },
            {
                'codename': 'can_approve_documents',
                'name': 'Can approve documents',
                'model': Document
            },
        ]
        
        # Create custom permissions if needed
        created_count = 0
        
        self.stdout.write("\n\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("  🔧 Creating Custom Permissions"))
        self.stdout.write("=" * 70)
        
        for perm_data in custom_permissions_data:
            content_type = ContentType.objects.get_for_model(perm_data['model'])
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                content_type=content_type,
                defaults={'name': perm_data['name']}
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ Created custom: {perm_data['name']}")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("  📊 Assigning Permissions to Roles"))
        self.stdout.write("=" * 70)
        
        # Define role-permission mappings using model permissions
        role_permissions = {
            'citizen': [
                # Basic user permissions - view and edit own profile
                'view_polauser',
                'change_polauser',
                'view_contact',
                'change_contact',
                'view_address',
                'change_address',
            ],
            'law_student': [
                # Student permissions - profile, documents, contacts
                'view_polauser',
                'change_polauser',
                'add_document',
                'view_document',
                'change_document',
                'delete_document',
                'view_contact',
                'change_contact',
                'add_contact',
                'view_address',
                'change_address',
                'add_address',
            ],
            'paralegal': [
                # Paralegal permissions - students + verification view
                'view_polauser',
                'change_polauser',
                'add_document',
                'view_document',
                'change_document',
                'delete_document',
                'view_contact',
                'change_contact',
                'add_contact',
                'view_address',
                'change_address',
                'add_address',
                'view_verification',
            ],
            'lawyer': [
                # Lawyer permissions - full document management + verification
                'view_polauser',
                'change_polauser',
                'add_document',
                'view_document',
                'change_document',
                'delete_document',
                'view_contact',
                'change_contact',
                'add_contact',
                'delete_contact',
                'view_address',
                'change_address',
                'add_address',
                'delete_address',
                'view_verification',
                'add_verification',
            ],
            'advocate': [
                # Advocate permissions - lawyers + verification management
                'view_polauser',
                'change_polauser',
                'add_document',
                'view_document',
                'change_document',
                'delete_document',
                'can_approve_documents',  # Custom permission
                'view_contact',
                'change_contact',
                'add_contact',
                'delete_contact',
                'view_address',
                'change_address',
                'add_address',
                'delete_address',
                'view_verification',
                'add_verification',
                'change_verification',
            ],
            'law_firm': [
                # Law firm permissions - full business management
                'view_polauser',
                'change_polauser',
                'add_polauser',  # Can add staff members
                'add_document',
                'view_document',
                'change_document',
                'delete_document',
                'can_approve_documents',  # Custom permission
                'view_contact',
                'change_contact',
                'add_contact',
                'delete_contact',
                'view_address',
                'change_address',
                'add_address',
                'delete_address',
                'view_verification',
                'add_verification',
                'change_verification',
            ],
        }
        
        # Assign permissions to roles
        assigned_count = 0
        for role_name, perm_codenames in role_permissions.items():
            try:
                role = UserRole.objects.get(role_name=role_name)
                
                for codename in perm_codenames:
                    result = role.assign_permission(codename)
                    if result:
                        self.stdout.write(f"  ✅ {role_name}: {codename}")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠️  {role_name}: {codename} (permission not found)")
                        )
                        
            except UserRole.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Role '{role_name}' does not exist. Run seed_user_roles first.")
                )
        
        # Assign permissions to staff (admin) users
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("  👤 Assigning Admin Permissions (is_staff=True)"))
        self.stdout.write("=" * 70)
        
        admin_permissions = [
            # Full user management
            'view_polauser',
            'add_polauser',
            'change_polauser',
            'delete_polauser',
            # Full document management
            'view_document',
            'add_document',
            'change_document',
            'delete_document',
            'can_approve_documents',
            # Full verification management
            'view_verification',
            'add_verification',
            'change_verification',
            'delete_verification',
            'can_verify_others',
            # Full contact/address management
            'view_contact',
            'add_contact',
            'change_contact',
            'delete_contact',
            'view_address',
            'add_address',
            'change_address',
            'delete_address',
        ]
        
        staff_users = PolaUser.objects.filter(is_staff=True, is_superuser=False)
        staff_count = staff_users.count()
        
        if staff_count > 0:
            for admin_user in staff_users:
                for codename in admin_permissions:
                    try:
                        # Get permission from any content type that has it
                        permission = Permission.objects.filter(codename=codename).first()
                        if permission:
                            admin_user.user_permissions.add(permission)
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠️  Could not assign {codename}: {str(e)}")
                        )
                
                self.stdout.write(f"  ✅ Assigned {len(admin_permissions)} permissions to admin: {admin_user.email}")
        else:
            self.stdout.write(self.style.WARNING("  ℹ️  No staff users found (is_staff=True, is_superuser=False)"))
        
        # Note about superusers
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("  🔑 Superuser Permissions"))
        self.stdout.write("=" * 70)
        superuser_count = PolaUser.objects.filter(is_superuser=True).count()
        self.stdout.write(f"  ℹ️  Superusers ({superuser_count}) automatically have ALL permissions")
        self.stdout.write("  ℹ️  No explicit permission assignment needed for is_superuser=True")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("  ✅ Permission Seeding Complete!"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"  🎯 Custom permissions created: {created_count}")
        self.stdout.write(f"  📊 Permissions assigned to {len(role_permissions)} roles")
        self.stdout.write(f"  👤 Admin users (staff) with permissions: {staff_count}")
        self.stdout.write(f"  🔑 Superusers (auto all permissions): {superuser_count}")
        self.stdout.write("=" * 70)
