"""
Management command to create missing verification records
Usage: python manage.py create_missing_verifications
"""

from django.core.management.base import BaseCommand
from authentication.models import PolaUser, Verification


class Command(BaseCommand):
    help = 'Create missing verification records for users who don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Only process users with specific role (advocate, lawyer, paralegal, law_firm, etc.)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        role_filter = options['role']
        
        self.stdout.write(
            self.style.SUCCESS('=== CREATE MISSING VERIFICATION RECORDS ===\n')
        )
        
        # Build queryset
        queryset = PolaUser.objects.filter(verification__isnull=True)
        
        if role_filter:
            queryset = queryset.filter(user_role__role_name=role_filter)
            self.stdout.write(f"Filtering by role: {role_filter}")
        
        users_without_verification = queryset
        total_found = users_without_verification.count()
        
        if total_found == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All users already have verification records!')
            )
            return
        
        self.stdout.write(f"Found {total_found} users without verification records:")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No records will be created\n"))
        
        created_count = 0
        error_count = 0
        
        for user in users_without_verification:
            role_name = user.user_role.role_name if user.user_role else 'No Role'
            
            try:
                if not dry_run:
                    # Create verification record
                    Verification.objects.create(user=user)
                    
                self.stdout.write(
                    f"✅ {'Would create' if dry_run else 'Created'} verification for: "
                    f"{user.email} ({role_name})"
                )
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Failed to create verification for: {user.email} ({role_name}) - Error: {e}"
                    )
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(f"📊 Would create {created_count} verification records")
        else:
            self.stdout.write(f"📊 Created {created_count} verification records")
            
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"❌ {error_count} errors occurred"))
        
        if not dry_run and created_count > 0:
            # Verify the fix
            remaining = PolaUser.objects.filter(verification__isnull=True)
            if role_filter:
                remaining = remaining.filter(user_role__role_name=role_filter)
            remaining_count = remaining.count()
            
            self.stdout.write(f"🔍 Users still without verification: {remaining_count}")
            
            if remaining_count == 0:
                self.stdout.write(
                    self.style.SUCCESS("🎉 SUCCESS: All users now have verification records!")
                )
            
            total_verifications = Verification.objects.count()
            self.stdout.write(f"📋 Total verification records: {total_verifications}")