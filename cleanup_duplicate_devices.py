"""
Clean up duplicate device registrations
Merge duplicate devices keeping the most recent one
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.device_models import UserDevice
from django.db.models import Count
from collections import defaultdict

def cleanup_duplicate_devices():
    """Remove duplicate device registrations for each user"""
    
    print("=" * 70)
    print("Cleaning Up Duplicate Devices")
    print("=" * 70)
    
    # Find users with duplicate devices
    users_with_duplicates = UserDevice.objects.values('user', 'fcm_token').annotate(
        count=Count('id')
    ).filter(count__gt=1, fcm_token__isnull=False).exclude(fcm_token='')
    
    print(f"\n📊 Found {users_with_duplicates.count()} FCM token duplicates")
    
    total_removed = 0
    total_kept = 0
    
    for dup in users_with_duplicates:
        user_id = dup['user']
        fcm_token = dup['fcm_token']
        count = dup['count']
        
        # Get all devices with this FCM token for this user
        devices = UserDevice.objects.filter(
            user_id=user_id,
            fcm_token=fcm_token
        ).order_by('-last_seen', '-created_at')
        
        # Keep the most recent one
        keep_device = devices.first()
        remove_devices = devices[1:]
        
        print(f"\n👤 User ID {user_id}:")
        print(f"   FCM Token: {fcm_token[:50]}...")
        print(f"   Total duplicates: {count}")
        print(f"   ✅ Keeping device ID {keep_device.id} (last seen: {keep_device.last_seen})")
        
        for device in remove_devices:
            print(f"   ❌ Removing device ID {device.id} (last seen: {device.last_seen})")
            device.delete()
            total_removed += 1
        
        total_kept += 1
        
        # Mark the kept device as current if user doesn't have another current device
        if not UserDevice.objects.filter(user_id=user_id, is_current_device=True).exists():
            keep_device.is_current_device = True
            keep_device.save()
            print(f"   🎯 Marked as current device")
    
    # Also check for device_id duplicates (less common but possible)
    device_id_duplicates = UserDevice.objects.values('user', 'device_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    print(f"\n📊 Found {device_id_duplicates.count()} device_id duplicates")
    
    for dup in device_id_duplicates:
        user_id = dup['user']
        device_id = dup['device_id']
        count = dup['count']
        
        # Get all devices with this device_id for this user
        devices = UserDevice.objects.filter(
            user_id=user_id,
            device_id=device_id
        ).order_by('-last_seen', '-created_at')
        
        # Keep the most recent one
        keep_device = devices.first()
        remove_devices = devices[1:]
        
        print(f"\n👤 User ID {user_id}:")
        print(f"   Device ID: {device_id}")
        print(f"   Total duplicates: {count}")
        print(f"   ✅ Keeping device ID {keep_device.id}")
        
        for device in remove_devices:
            print(f"   ❌ Removing device ID {device.id}")
            device.delete()
            total_removed += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Cleanup Complete!")
    print(f"   Devices kept: {total_kept}")
    print(f"   Devices removed: {total_removed}")
    print("=" * 70)
    
    # Show summary per user
    print("\n📊 Device Summary per User:")
    print("-" * 70)
    
    from authentication.models import PolaUser
    
    users_with_devices = UserDevice.objects.values('user').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for user_data in users_with_devices[:10]:
        user_id = user_data['user']
        device_count = user_data['count']
        
        try:
            user = PolaUser.objects.get(id=user_id)
            current_device = UserDevice.objects.filter(user=user, is_current_device=True).first()
            current_name = current_device.device_name if current_device else "None"
            
            print(f"   {user.email:30s} - {device_count} device(s) - Current: {current_name}")
        except:
            pass

if __name__ == '__main__':
    cleanup_duplicate_devices()
