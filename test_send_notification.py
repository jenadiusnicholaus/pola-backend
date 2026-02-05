"""
Test sending notification to a specific user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from authentication.models import PolaUser
from notification.notification_service import NotificationService

def test_send_notification():
    """Send a test notification to micheal@gmail.com"""
    
    print("=" * 70)
    print("Testing Notification System")
    print("=" * 70)
    
    # Get the user
    try:
        user = PolaUser.objects.get(email='micheal@gmail.com')
        print(f"\n✅ Found user: {user.get_full_name()} (@{user.username})")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
    except PolaUser.DoesNotExist:
        print("\n❌ User micheal@gmail.com not found!")
        return
    
    # Check if user has FCM tokens
    from authentication.device_models import UserDevice
    devices = UserDevice.objects.filter(user=user, is_active=True)
    print(f"\n📱 Active devices: {devices.count()}")
    for device in devices:
        print(f"   - {device.device_name} ({device.device_type})")
        print(f"     FCM Token: {device.fcm_token[:50]}..." if device.fcm_token else "     No FCM Token")
    
    if devices.count() == 0:
        print("\n⚠️  Warning: User has no active devices registered!")
        print("   FCM push notification will not be sent, but notification will be saved to database.")
    
    # Initialize notification service
    notification_service = NotificationService()
    
    # Send test notification
    print("\n📤 Sending test notification...")
    
    success = notification_service.send_notification_to_user(
        user=user,
        notification_type='test',
        title='🔔 Test Notification',
        body=f'Hello {user.get_full_name()}! This is a test notification from the POLA backend.',
        data={
            'test': True,
            'timestamp': str(django.utils.timezone.now()),
            'message': 'If you can see this, notifications are working!'
        }
    )
    
    if success:
        print("\n✅ SUCCESS! Notification sent successfully!")
    else:
        print("\n⚠️  Notification saved to database but FCM push may have failed")
    
    # Check database
    from notification.models import UserNotification
    latest_notification = UserNotification.objects.filter(user=user).order_by('-created_at').first()
    
    if latest_notification:
        print("\n📊 Latest notification in database:")
        print(f"   ID: {latest_notification.id}")
        print(f"   Type: {latest_notification.notification_type}")
        print(f"   Title: {latest_notification.title}")
        print(f"   Body: {latest_notification.body}")
        print(f"   FCM Sent: {latest_notification.fcm_sent}")
        print(f"   Read: {latest_notification.is_read}")
        print(f"   Created: {latest_notification.created_at}")
        print(f"   Data: {latest_notification.data}")
    
    # Show how to fetch via API
    print("\n" + "=" * 70)
    print("To fetch this notification via API:")
    print("=" * 70)
    print(f"\nGET http://localhost:8000/api/v1/notifications/")
    print(f"Authorization: Bearer <micheal's_token>")
    print("\nOr get unread count:")
    print(f"GET http://localhost:8000/api/v1/notifications/unread_count/")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == '__main__':
    test_send_notification()
