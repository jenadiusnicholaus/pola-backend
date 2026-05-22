#!/usr/bin/env python
"""
Production seeding script for POLA Backend
Run this to populate test data in production
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.core.management import call_command
from authentication.models import PolaUser, UserRole

def create_super_admin():
    """Create super admin user"""
    try:
        if PolaUser.objects.filter(email='admin@gmail.com').exists():
            print("⚠️  Super admin already exists: admin@gmail.com")
            return

        print("👤 Creating super admin...")
        admin_user = PolaUser.objects.create_superuser(
            email='admin@gmail.com',
            password='1234',
            first_name='Super',
            last_name='Admin'
        )
        print(f"✅ Super admin created: {admin_user.email}")
        print(f"   Password: 1234")
    except Exception as e:
        print(f"❌ Error creating super admin: {e}")

def run_seed_commands():
    """Run essential seeding commands for production testing"""

    print("🌱 Starting production seeding...")

    # Create super admin first
    create_super_admin()

    # Core authentication data
    try:
        print("📋 Seeding user roles...")
        call_command('seed_user_roles')
        print("✅ User roles seeded")
    except Exception as e:
        print(f"❌ Error seeding user roles: {e}")

    try:
        print("🌍 Seeding regions and districts...")
        call_command('seed_regions_districts')
        print("✅ Regions and districts seeded")
    except Exception as e:
        print(f"❌ Error seeding regions: {e}")

    try:
        print("⚖️ Seeding specializations...")
        call_command('seed_specializations')
        print("✅ Specializations seeded")
    except Exception as e:
        print(f"❌ Error seeding specializations: {e}")

    try:
        print("🏢 Seeding place of work...")
        call_command('seed_place_of_work')
        print("✅ Place of work seeded")
    except Exception as e:
        print(f"❌ Error seeding place of work: {e}")

    try:
        print("📋 Seeding permissions...")
        call_command('seed_permissions')
        print("✅ Permissions seeded")
    except Exception as e:
        print(f"❌ Error seeding permissions: {e}")

    # Subscription data
    try:
        print("💳 Seeding subscription plans...")
        call_command('seed_subscription_plans')
        print("✅ Subscription plans seeded")
    except Exception as e:
        print(f"❌ Error seeding subscription plans: {e}")

    try:
        print("👨‍⚖️ Seeding consultants...")
        call_command('seed_consultants')
        print("✅ Consultants seeded")
    except Exception as e:
        print(f"❌ Error seeding consultants: {e}")

    # Document templates
    try:
        print("📄 Seeding document templates...")
        call_command('seed_templates')
        print("✅ Document templates seeded")
    except Exception as e:
        print(f"❌ Error seeding templates: {e}")

    # Hubs data
    try:
        print("🏛️ Seeding hubs...")
        call_command('seed_hubs')
        print("✅ Hubs seeded")
    except Exception as e:
        print(f"❌ Error seeding hubs: {e}")

    try:
        print("❓ Seeding hub questions...")
        call_command('seed_questions')
        print("✅ Hub questions seeded")
    except Exception as e:
        print(f"❌ Error seeding questions: {e}")

    # Document fields
    try:
        print("📝 Seeding notice fields...")
        os.system('python seed_notice_fields.py')
        print("✅ Notice fields seeded")
    except Exception as e:
        print(f"❌ Error seeding notice fields: {e}")

    try:
        print("📋 Seeding questionnaire fields...")
        os.system('python seed_questionnaire_fields.py')
        print("✅ Questionnaire fields seeded")
    except Exception as e:
        print(f"❌ Error seeding questionnaire fields: {e}")

    print("\n🎉 Production seeding completed!")
    print("📊 Summary:")
    print("  - Super admin (admin@gmail.com / 1234)")
    print("  - User roles and permissions")
    print("  - Geographic data (regions/districts)")
    print("  - Legal specializations")
    print("  - Place of work")
    print("  - Subscription plans")
    print("  - Test consultants")
    print("  - Document templates")
    print("  - Hub data and questions")
    print("  - Document field templates")

if __name__ == '__main__':
    run_seed_commands()
