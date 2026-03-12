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

def run_seed_commands():
    """Run essential seeding commands for production testing"""
    
    print("🌱 Starting production seeding...")
    
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
    print("  - User roles and permissions")
    print("  - Geographic data (regions/districts)")
    print("  - Legal specializations")
    print("  - Subscription plans")
    print("  - Test consultants")
    print("  - Document templates")
    print("  - Hub data and questions")
    print("  - Document field templates")

if __name__ == '__main__':
    run_seed_commands()
