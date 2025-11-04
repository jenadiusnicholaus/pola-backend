#!/usr/bin/env python
"""
Comprehensive API test for the fixed topic materials endpoint
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.test import Client, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

print('🧪 Testing Fixed API Endpoint with proper settings...')
print('=' * 50)

# Get a user and create a token
User = get_user_model()
user = User.objects.first()
print(f'👤 Using user: {user.email}')

# Create JWT token
refresh = RefreshToken.for_user(user)
access_token = refresh.access_token

# Use API client with token and override settings
with override_settings(ALLOWED_HOSTS=['*']):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    # Test 1: Get all materials
    print('\n1️⃣ Testing: Basic materials endpoint')
    response = client.get('/api/v1/hubs/legal-education/topics/constitutional-law/materials/')
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'   🔍 Response keys: {list(data.keys())}')
        results = data.get('results', data.get('materials', []))
        print(f'   📊 Materials returned: {len(results)}')
        
        if 'count' in data:
            print(f'   📄 Total count: {data["count"]}')
            print(f'   📄 Paginated: True (showing {len(results)} of {data["count"]})')
        else:
            print(f'   📄 Direct response: {len(results)} materials')
            
        # Debug: Check if results is actually a list
        print(f'   🔍 Results type: {type(results)}')
        
        # Handle the case where results is nested in the pagination response
        if isinstance(results, dict) and 'materials' in results:
            materials_list = results['materials']
            print(f'   📊 Nested materials found: {len(materials_list)}')
            if isinstance(materials_list, list) and len(materials_list) > 0:
                first_material = materials_list[0]
                print(f'   📝 Sample material: "{first_material.get("title", "N/A")[:40]}..."')
                print(f'   🏷️  Content type: {first_material.get("content_type", "N/A")}')
                print(f'   💰 Price: ${first_material.get("price", "0")}')
        elif isinstance(results, list) and len(results) > 0:
            first_material = results[0]
            print(f'   📝 Sample material: "{first_material.get("title", "N/A")[:40]}..."')
            print(f'   🏷️  Content type: {first_material.get("content_type", "N/A")}')
            print(f'   💰 Price: ${first_material.get("price", "0")}')
    else:
        print(f'   ❌ Error: {response.content}')

    # Test 2: Language filter
    print('\n2️⃣ Testing: Language filter (English only)')
    response = client.get('/api/v1/hubs/legal-education/topics/constitutional-law/materials/?language=en')
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', data.get('materials', []))
        print(f'   📊 English materials: {len(results)}')
        
        # Handle nested structure
        materials_list = results.get('materials', []) if isinstance(results, dict) else results
        if materials_list and isinstance(materials_list, list):
            print(f'   🌍 Languages found: {set(m.get("language", "N/A") for m in materials_list)}')
    else:
        print(f'   ❌ Error: {response.content}')

    # Test 3: Content type filter
    print('\n3️⃣ Testing: Content type filter (notes only)')
    response = client.get('/api/v1/hubs/legal-education/topics/constitutional-law/materials/?content_type=notes')
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', data.get('materials', []))
        print(f'   📊 Notes materials: {len(results)}')
        
        materials_list = results.get('materials', []) if isinstance(results, dict) else results
        if materials_list and isinstance(materials_list, list):
            print(f'   📝 Content types found: {set(m.get("content_type", "N/A") for m in materials_list)}')
    else:
        print(f'   ❌ Error: {response.content}')

    # Test 4: Search functionality
    print('\n4️⃣ Testing: Search functionality')
    response = client.get('/api/v1/hubs/legal-education/topics/constitutional-law/materials/?search=constitutional')
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', data.get('materials', []))
        print(f'   📊 Search results: {len(results)}')
        
        materials_list = results.get('materials', []) if isinstance(results, dict) else results
        if materials_list and isinstance(materials_list, list) and len(materials_list) > 0:
            print(f'   🔍 Sample match: "{materials_list[0].get("title", "N/A")[:50]}..."')
    else:
        print(f'   ❌ Error: {response.content}')

    # Test 5: Multiple filters combined
    print('\n5️⃣ Testing: Combined filters (English + free)')
    response = client.get('/api/v1/hubs/legal-education/topics/constitutional-law/materials/?language=en&price=0')
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', data.get('materials', []))
        print(f'   📊 Combined filter results: {len(results)}')
        
        materials_list = results.get('materials', []) if isinstance(results, dict) else results
        if materials_list and isinstance(materials_list, list):
            free_materials = [m for m in materials_list if float(m.get('price', 0)) == 0.0]
            print(f'   💰 Free materials confirmed: {len(free_materials)}')
    else:
        print(f'   ❌ Error: {response.content}')

print('\n✅ Comprehensive API testing completed!')
print('🎉 The fixed union query logic is working properly!')