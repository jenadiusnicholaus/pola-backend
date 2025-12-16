#!/usr/bin/env python
"""
Test role-based permissions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.models import PolaUser

def test_user_permissions(email):
    """Test permissions for a specific user"""
    try:
        user = PolaUser.objects.get(email=email)
        
        print("\n" + "="*70)
        print(f"USER: {email}")
        print("="*70)
        
        # User info
        print(f"\nRole: {user.user_role.get_role_display() if user.user_role else 'No role'}")
        print(f"Role Name: {user.user_role.role_name if user.user_role else 'None'}")
        
        # Check if professional
        is_prof = user.user_role and user.user_role.role_name in ['advocate', 'lawyer', 'paralegal', 'law_firm']
        print(f"Is Professional: {is_prof}")
        
        # Subscription
        subscription = user.subscription
        print(f"\nPlan: {subscription.plan.name}")
        print(f"Active: {subscription.is_active()}")
        print(f"Type: {subscription.plan.plan_type}")
        
        # Get permissions
        permissions = subscription.get_permissions()
        
        print("\n" + "-"*70)
        print("SUBSCRIPTION-BASED PERMISSIONS")
        print("-"*70)
        print(f"✅ Legal Library: {permissions.get('can_access_legal_library')}")
        print(f"✅ Ask Questions: {permissions.get('can_ask_questions')} ({permissions.get('questions_remaining')} remaining)")
        print(f"✅ Generate Documents: {permissions.get('can_generate_documents')} ({permissions.get('documents_remaining')} remaining)")
        print(f"✅ Forum Access: {permissions.get('can_access_forum')}")
        print(f"✅ Student Hub: {permissions.get('can_access_student_hub')}")
        print(f"✅ Legal Updates: {permissions.get('can_receive_legal_updates')}")
        
        print("\n" + "-"*70)
        print("ROLE-BASED PERMISSIONS")
        print("-"*70)
        print(f"{'✅' if permissions.get('can_view_talk_to_lawyer') else '❌'} View 'Talk to Lawyer' Page: {permissions.get('can_view_talk_to_lawyer')}")
        print(f"{'✅' if permissions.get('can_view_nearby_lawyers') else '❌'} View Nearby Lawyers: {permissions.get('can_view_nearby_lawyers')}")
        print(f"✅ View Own Consultations: {permissions.get('can_view_own_consultations')}")
        
        print("\n" + "-"*70)
        print("PURCHASE PERMISSIONS")
        print("-"*70)
        print(f"✅ Purchase Consultations: {permissions.get('can_purchase_consultations')}")
        print(f"✅ Purchase Documents: {permissions.get('can_purchase_documents')}")
        print(f"✅ Purchase Materials: {permissions.get('can_purchase_learning_materials')}")
        
        print("\n" + "="*70)
        
    except PolaUser.DoesNotExist:
        print(f"\n❌ User {email} not found")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Test rama@gmail.com (lecturer)
    test_user_permissions('rama@gmail.com')
    
    # You can add more test users here
    # test_user_permissions('professional@example.com')
    # test_user_permissions('citizen@example.com')
