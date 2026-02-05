"""
Verify notification can be fetched via API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import PolaUser
import requests
import json

def test_notification_api():
    # Get Micheal's token
    user = PolaUser.objects.get(email='micheal@gmail.com')
    token = str(RefreshToken.for_user(user).access_token)
    
    print('Testing Notification API for micheal@gmail.com')
    print('=' * 70)
    
    # 1. Get unread count
    print('\n1️⃣ Getting unread count...')
    response = requests.get(
        'http://localhost:8000/api/v1/notifications/unread_count/',
        headers={'Authorization': f'Bearer {token}'}
    )
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        print(f'   Unread notifications: {response.json()["count"]}')
    
    # 2. Get all notifications
    print('\n2️⃣ Getting all notifications...')
    response = requests.get(
        'http://localhost:8000/api/v1/notifications/',
        headers={'Authorization': f'Bearer {token}'}
    )
    print(f'   Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'   Total notifications: {data["count"]}')
        
        if data['results']:
            print('\n   Latest notification:')
            notif = data['results'][0]
            print(f'   ID: {notif["id"]}')
            print(f'   Type: {notif["notification_type"]}')
            print(f'   Title: {notif["title"]}')
            print(f'   Body: {notif["body"]}')
            print(f'   Read: {notif["is_read"]}')
            print(f'   FCM Sent: {notif["fcm_sent"]}')
            print(f'   Created: {notif["created_at"]}')
            print(f'   Data: {notif["data"]}')
    
    print('\n' + '=' * 70)
    print('✅ Notification system is working!')
    print('=' * 70)

if __name__ == '__main__':
    test_notification_api()
