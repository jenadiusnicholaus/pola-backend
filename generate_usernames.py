"""
Generate unique usernames for all existing users who don't have one
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.models import PolaUser

def generate_usernames():
    """Generate usernames for all users without one"""
    users_without_username = PolaUser.objects.filter(username__isnull=True) | PolaUser.objects.filter(username='')
    count = users_without_username.count()
    
    print(f"\n🔍 Found {count} users without usernames")
    
    if count == 0:
        print("✅ All users already have usernames!")
        return
    
    print("\n⚙️  Generating usernames...")
    
    updated = 0
    for user in users_without_username:
        old_username = user.username
        # The save() method will auto-generate username
        user.save()
        print(f"  • {user.email} → @{user.username}")
        updated += 1
    
    print(f"\n✅ Successfully generated {updated} usernames!")
    
    # Verify all users now have usernames
    remaining = PolaUser.objects.filter(username__isnull=True).count()
    if remaining == 0:
        print("✅ All users now have unique usernames!")
    else:
        print(f"⚠️  Warning: {remaining} users still without usernames")

if __name__ == '__main__':
    generate_usernames()
