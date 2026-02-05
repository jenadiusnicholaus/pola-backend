"""
Clean up duplicate devices using fingerprint matching
Merge devices with same name + model for each user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.device_models import UserDevice
from authentication.models import PolaUser
from django.db.models import Count

def cleanup_by_fingerprint():
    """Remove duplicate devices based on device fingerprint (name + model)"""
    
    print("=" * 80)
    print("Cleaning Up Duplicate Devices by Fingerprint")
    print("=" * 80)
    
    # Get all users
    users = PolaUser.objects.filter(devices__isnull=False).distinct()
    
    total_removed = 0
    total_users_cleaned = 0
    
    for user in users:
        # Group devices by fingerprint (name + model)
        devices = UserDevice.objects.filter(user=user, is_active=True)
        
        # Group by fingerprint
        fingerprints = {}
        for device in devices:
            key = f"{device.device_name}|{device.device_model}"
            if key not in fingerprints:
                fingerprints[key] = []
            fingerprints[key].append(device)
        
        # Find duplicates
        user_had_duplicates = False
        for fingerprint, device_list in fingerprints.items():
            if len(device_list) > 1:
                if not user_had_duplicates:
                    print(f"\n👤 {user.email} (ID: {user.id})")
                    user_had_duplicates = True
                    total_users_cleaned += 1
                
                # Sort by last_seen (keep most recent)
                device_list.sort(key=lambda d: d.last_seen or d.created_at, reverse=True)
                
                keep_device = device_list[0]
                remove_devices = device_list[1:]
                
                device_name, device_model = fingerprint.split('|')
                print(f"\n   📱 Device: {device_name} (Model: {device_model or 'unknown'})")
                print(f"      Found {len(device_list)} duplicates")
                print(f"      ✅ Keeping device ID {keep_device.id}")
                print(f"         - Last seen: {keep_device.last_seen}")
                print(f"         - FCM token: {keep_device.fcm_token[:40] if keep_device.fcm_token else 'None'}...")
                print(f"         - Device ID: {keep_device.device_id}")
                
                # Merge FCM tokens if the kept device doesn't have one
                if not keep_device.fcm_token:
                    for device in remove_devices:
                        if device.fcm_token:
                            keep_device.fcm_token = device.fcm_token
                            print(f"         - Updated FCM token from device {device.id}")
                            break
                
                # Merge coordinates if needed
                if not keep_device.latitude and not keep_device.longitude:
                    for device in remove_devices:
                        if device.latitude or device.longitude:
                            keep_device.latitude = device.latitude
                            keep_device.longitude = device.longitude
                            print(f"         - Updated coordinates from device {device.id}")
                            break
                
                keep_device.save()
                
                # Remove duplicates
                for device in remove_devices:
                    print(f"      ❌ Removing device ID {device.id}")
                    print(f"         - Last seen: {device.last_seen}")
                    print(f"         - FCM token: {device.fcm_token[:40] if device.fcm_token else 'None'}...")
                    device.delete()
                    total_removed += 1
        
        # Ensure user has exactly one current device
        if user_had_duplicates:
            current_devices = UserDevice.objects.filter(user=user, is_current_device=True)
            if current_devices.count() == 0:
                # No current device, mark most recent as current
                most_recent = UserDevice.objects.filter(user=user, is_active=True).order_by('-last_seen').first()
                if most_recent:
                    most_recent.is_current_device = True
                    most_recent.save()
                    print(f"   🎯 Marked device {most_recent.id} as current device")
            elif current_devices.count() > 1:
                # Multiple current devices, keep only most recent
                keep_current = current_devices.order_by('-last_seen').first()
                current_devices.exclude(id=keep_current.id).update(is_current_device=False)
                print(f"   🎯 Kept only device {keep_current.id} as current device")
    
    print("\n" + "=" * 80)
    print(f"✅ Cleanup Complete!")
    print(f"   Users cleaned: {total_users_cleaned}")
    print(f"   Devices removed: {total_removed}")
    print("=" * 80)
    
    # Final summary
    print("\n📊 Final Device Count per User:")
    print("-" * 80)
    
    users_with_devices = UserDevice.objects.values('user__email', 'user__id').annotate(
        count=Count('id')
    ).filter(count__gt=0).order_by('-count')
    
    for item in users_with_devices[:15]:
        email = item['user__email']
        count = item['count']
        user_id = item['user__id']
        
        current_device = UserDevice.objects.filter(
            user_id=user_id,
            is_current_device=True
        ).first()
        
        current_name = current_device.device_name if current_device else "No current device"
        
        print(f"   {email:35s} - {count} device(s) - Current: {current_name}")

if __name__ == '__main__':
    cleanup_by_fingerprint()
