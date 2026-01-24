"""
Test comment API to verify username is included in author info and mentions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import PolaUser
import requests
import json

def test_comment_username():
    """Test that comments include username in author_info and mentions"""
    
    # Get test user
    user = PolaUser.objects.get(email='rama@gmail.com')
    token = str(RefreshToken.for_user(user).access_token)
    
    headers = {'Authorization': f'Bearer {token}'}
    
    print("=" * 60)
    print("Testing Comment API - Username Field")
    print("=" * 60)
    
    # Test 1: Get comments list
    print("\n1️⃣ Testing GET /api/v1/hubs/comments/ (List)")
    response = requests.get(
        'http://localhost:8000/api/v1/hubs/comments/?hub_type=forum&limit=1',
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            comment = data['results'][0]
            author = comment['author_info']
            
            print(f"   Status: ✅ {response.status_code}")
            print(f"   Author ID: {author['id']}")
            print(f"   Author Email: {author['email']}")
            print(f"   Author Username: {author.get('username', 'MISSING!')}")
            print(f"   Author Full Name: {author['full_name']}")
            
            if 'username' in author:
                print(f"\n   ✅ Author has username field: @{author['username']}")
            else:
                print(f"\n   ❌ Author MISSING username field!")
        else:
            print("   ⚠️  No comments found to test")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Test 2: Create comment with mention
    print("\n2️⃣ Testing POST /api/v1/hubs/comments/ (Create with mention)")
    other_user = PolaUser.objects.exclude(id=user.id).first()
    
    response = requests.post(
        'http://localhost:8000/api/v1/hubs/comments/',
        headers={**headers, 'Content-Type': 'application/json'},
        json={
            'hub_type': 'forum',
            'content': 1,
            'comment_text': f'Testing @{other_user.username} username field!',
            'mentioned_users': [other_user.id]
        }
    )
    
    if response.status_code == 201:
        comment = response.json()
        author = comment['author_info']
        
        print(f"   Status: ✅ {response.status_code}")
        print(f"   Comment ID: {comment['id']}")
        print(f"\n   Author Info:")
        print(f"   - Username: @{author.get('username', 'MISSING!')}")
        print(f"   - Full Name: {author['full_name']}")
        
        if comment.get('mentions'):
            print(f"\n   Mentions ({len(comment['mentions'])} users):")
            for mention in comment['mentions']:
                print(f"   - User ID: {mention['user_id']}")
                print(f"     Username: @{mention.get('username', 'MISSING!')}")
                print(f"     Full Name: {mention['full_name']}")
                print(f"     Position: {mention['position']}")
            
            if all('username' in m for m in comment['mentions']):
                print(f"\n   ✅ All mentions have username field!")
            else:
                print(f"\n   ❌ Some mentions MISSING username field!")
        else:
            print(f"\n   ⚠️  No mentions in comment")
            
        if 'username' in author and comment.get('mentions') and all('username' in m for m in comment['mentions']):
            print("\n" + "=" * 60)
            print("✅ SUCCESS: All comment data includes username!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ FAILED: Some data missing username!")
            print("=" * 60)
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
    
    # Test 3: User search
    print("\n3️⃣ Testing GET /api/v1/hubs/mentions/users/search/ (User search)")
    response = requests.get(
        'http://localhost:8000/api/v1/hubs/mentions/users/search/?q=ra&limit=3',
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: ✅ {response.status_code}")
        print(f"   Found: {len(data['results'])} users")
        
        for idx, user_data in enumerate(data['results'][:3], 1):
            print(f"\n   User {idx}:")
            print(f"   - Username: @{user_data.get('username', 'MISSING!')}")
            print(f"   - Full Name: {user_data['full_name']}")
            print(f"   - Email: {user_data['email']}")
        
        if all('username' in u for u in data['results']):
            print(f"\n   ✅ All search results have username!")
        else:
            print(f"\n   ❌ Some search results MISSING username!")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_comment_username()
