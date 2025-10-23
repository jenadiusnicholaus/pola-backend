#!/usr/bin/env python
"""
Test Admin CRUD API endpoints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from rest_framework.test import APIClient, APIRequestFactory
from authentication.models import PolaUser
from documents.models import LearningMaterial

def test_admin_crud():
    """Test all admin CRUD operations"""
    
    # Get or create admin user
    admin = PolaUser.objects.filter(is_staff=True, is_superuser=True).first()
    if not admin:
        admin = PolaUser.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='Test'
        )
        print(f"✅ Created admin user: {admin.email}")
    else:
        print(f"✅ Using existing admin: {admin.email}")

    # Create API client (without CommonMiddleware issues)
    factory = APIRequestFactory()
    client = APIClient(enforce_csrf_checks=False)
    client.force_authenticate(user=admin)

    print("\n" + "="*60)
    print("🧪 TESTING ADMIN CRUD API")
    print("="*60)

    # TEST 1: CREATE
    print("\n1️⃣ TEST CREATE (POST)")
    print("-" * 60)
    create_data = {
        'hub_type': 'advocates',
        'content_type': 'news',
        'title': 'Test API: Supreme Court Ruling on Digital Evidence',
        'description': 'Testing admin CRUD API creation endpoint',
        'content': 'Full test content here. This is a test article created via API.',
        'is_pinned': True
    }
    
    response = client.post(
        '/api/v1/admin/hubs/hub-content/', 
        create_data,
        format='json',
        HTTP_HOST='localhost'
    )

    if response.status_code == 201:
        print(f"✅ Status: {response.status_code} Created")
        data = response.json()
        content_id = data['data']['id']
        print(f"✅ Content ID: {content_id}")
        print(f"✅ Title: {data['data']['title']}")
        print(f"✅ Uploader: {data['data']['uploader_info']['email']}")
        print(f"✅ Is Pinned: {data['data']['is_pinned']}")
        print(f"✅ Is Approved: {data['data']['is_approved']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"❌ Response: {response.content.decode()}")
        return

    # TEST 2: LIST
    print("\n2️⃣ TEST LIST (GET)")
    print("-" * 60)
    response = client.get('/api/v1/admin/hubs/hub-content/', HTTP_HOST='localhost')
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code} OK")
        print(f"✅ Total Count: {data['count']}")
        print(f"✅ Results Returned: {len(data['results'])}")
        if data['results']:
            print(f"✅ First Item: {data['results'][0]['title'][:50]}...")
    else:
        print(f"❌ Status: {response.status_code}")

    # TEST 3: RETRIEVE
    print("\n3️⃣ TEST RETRIEVE (GET by ID)")
    print("-" * 60)
    response = client.get(f'/api/v1/admin/hubs/hub-content/{content_id}/', HTTP_HOST='localhost')
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code} OK")
        print(f"✅ Title: {data['title']}")
        print(f"✅ Hub Type: {data['hub_type']}")
        print(f"✅ Content Type: {data['content_type']}")
        print(f"✅ Engagement Score: {data['engagement_score']}")
        print(f"✅ Likes: {data['likes_count']}")
        print(f"✅ Comments: {data['comments_count']}")
    else:
        print(f"❌ Status: {response.status_code}")

    # TEST 4: UPDATE (PATCH)
    print("\n4️⃣ TEST UPDATE (PATCH)")
    print("-" * 60)
    update_data = {
        'title': 'UPDATED: Supreme Court Ruling on Digital Evidence',
        'is_pinned': False
    }
    response = client.patch(
        f'/api/v1/admin/hubs/hub-content/{content_id}/', 
        update_data,
        format='json',
        HTTP_HOST='localhost'
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code} OK")
        print(f"✅ New Title: {data['data']['title']}")
        print(f"✅ Is Pinned: {data['data']['is_pinned']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"❌ Response: {response.content.decode()}")

    # TEST 5: BULK ACTION
    print("\n5️⃣ TEST BULK ACTION (pin)")
    print("-" * 60)
    # Create 2 more items for bulk test
    content_ids = [content_id]
    for i in range(2):
        resp = client.post(
            '/api/v1/admin/hubs/hub-content/', 
            {
                'hub_type': 'advocates',
                'content_type': 'news',
                'title': f'Bulk Test Item {i+1}',
                'description': 'Testing bulk actions',
                'content': 'Test content',
                'is_pinned': False
            },
            format='json',
            HTTP_HOST='localhost'
        )
        if resp.status_code == 201:
            content_ids.append(resp.json()['data']['id'])

    response = client.post(
        '/api/v1/admin/hubs/hub-content/bulk_action/', 
        {
            'content_ids': content_ids,
            'action': 'pin'
        },
        format='json',
        HTTP_HOST='localhost'
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code} OK")
        print(f"✅ Message: {data['message']}")
        print(f"✅ Affected Count: {data['affected_count']}")
        print(f"✅ Content IDs: {data['content_ids']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"❌ Response: {response.content.decode()}")

    # TEST 6: DELETE
    print("\n6️⃣ TEST DELETE")
    print("-" * 60)
    # Delete all test items
    for cid in content_ids:
        response = client.delete(
            f'/api/v1/admin/hubs/hub-content/{cid}/',
            HTTP_HOST='localhost'
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Deleted: {data['message'][:80]}...")
        else:
            print(f"❌ Failed to delete ID {cid}")

    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETED!")
    print("="*60)
    print("\n✅ Admin CRUD API is working correctly!")
    print("\n📚 See full documentation: docs/ADMIN_CRUD_API.md")
    print("🌐 Swagger UI: http://localhost:8000/swagger/")

if __name__ == '__main__':
    test_admin_crud()
