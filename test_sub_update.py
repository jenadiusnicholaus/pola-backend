import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from rest_framework.test import APIClient
from subscriptions.models import UserSubscription
from authentication.models import PolaUser
from rest_framework import status

def run_tests():
    print("🧪 Testing Admin Subscription Update\n")
    client = APIClient()
    admin_user = PolaUser.objects.filter(is_superuser=True).first() or PolaUser.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ Error: No staff/superuser found.")
        return
    client.force_authenticate(user=admin_user)
    
    # Get a subscription to test on
    sub = UserSubscription.objects.first()
    if not sub:
        print("❌ No subscriptions found in DB")
        return
        
    print(f"Original End Date: {sub.end_date}, Status: {sub.status}")
    
    # Try updating the subscription's end_date
    patch_data = {
        'status': 'active',
        'end_date': '2027-12-31T23:59:59Z'
    }
    
    response = client.patch(f'/api/v1/admin/subscriptions/users/{sub.id}/', patch_data, format='json')
    if response.status_code == status.HTTP_200_OK:
        print(f"✅ Subscription updated! New status: {response.data.get('status')}, New end date: {response.data.get('end_date')}")
        
        # Optionally put it back
        patch_data_revert = {
            'status': sub.status,
            'end_date': sub.end_date.isoformat() if sub.end_date else None
        }
        client.patch(f'/api/v1/admin/subscriptions/users/{sub.id}/', patch_data_revert, format='json')
        print("Reverted to original state.")
    else:
        print(f"❌ Update failed! {response.status_code}")
        print(response.data)

if __name__ == "__main__":
    run_tests()
