#!/usr/bin/env python
"""
Test script to verify the newly created Constitutional Law materials
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def test_constitutional_materials():
    """Test the constitutional law materials API endpoint"""
    
    print("🧪 TESTING CONSTITUTIONAL LAW MATERIALS API")
    print("=" * 50)
    
    # Step 1: Get user and create JWT token
    print("1️⃣ Setting up authentication...")
    try:
        User = get_user_model()
        user = User.objects.first()
        print(f"✅ Using user: {user.email}")
        
        # Create JWT token
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        print("✅ JWT token created")
            
    except Exception as e:
        print(f"❌ Authentication setup error: {e}")
        return
    
    # Step 2: Get Constitutional Law materials
    print("\n2️⃣ Fetching Constitutional Law materials...")
    try:
        # Use API client with token and override settings
        with override_settings(ALLOWED_HOSTS=['*']):
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Get materials
            response = client.get('/api/v1/hubs/legal-education/topics/constitutional-law/materials/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Materials retrieved successfully!")
            
            # Extract materials from the nested response structure
            results_data = data.get('results', {})
            materials = results_data.get('materials', [])
            count = results_data.get('materials_count', len(materials))
            
            print(f"\n📊 Found {count} materials in Constitutional Law:")
            print("-" * 40)
            
            for i, material in enumerate(materials, 1):
                content_type = material.get('content_type', 'unknown')
                title = material.get('title', 'No title')
                price = float(material.get('price', 0))
                has_file = bool(material.get('file'))
                has_content = bool(material.get('content', '').strip())
                
                # Determine viewer type based on content
                if has_file:
                    file_url = material.get('file', '')
                    if '.pdf' in file_url.lower():
                        viewer_type = "📄 PDF Viewer"
                    else:
                        viewer_type = "📎 File Viewer"
                elif has_content:
                    viewer_type = "📝 Document Reader"
                else:
                    viewer_type = "❓ Unknown"
                
                price_info = f"💰 {price:.0f} TZS" if price > 0 else "🆓 FREE"
                
                print(f"\n{i}. {title}")
                print(f"   Content Type: {content_type}")
                print(f"   Viewer Type: {viewer_type}")
                print(f"   Price: {price_info}")
                print(f"   Has File: {'✅' if has_file else '❌'}")
                print(f"   Has Rich Content: {'✅' if has_content else '❌'}")
                
                if has_file:
                    file_url = material.get('file')
                    print(f"   📎 File URL: {file_url}")
                
                if has_content:
                    content_preview = material.get('content', '')[:150] + "..." if len(material.get('content', '')) > 150 else material.get('content', '')
                    print(f"   📝 Content Preview: {content_preview}")
                
                print(f"   🆔 Material ID: {material.get('id')}")
            
            print(f"\n🎯 Flutter Testing Guide:")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"📱 For PDF Viewer Testing:")
            print(f"   • Use materials with 'Has File: ✅' and PDF in file URL")
            print(f"   • These materials have a 'file' field with PDF URL")
            print(f"   • Implement PDF viewer component for these materials")
            print()
            print(f"📖 For Document Reader Testing:")
            print(f"   • Use materials with 'Has Rich Content: ✅'")
            print(f"   • These materials have rich HTML content in 'content' field")
            print(f"   • Implement rich text/HTML viewer for these materials")
            print()
            print(f"🔧 Implementation Tips:")
            print(f"   • Check 'content_type' field for material categorization")
            print(f"   • Use 'file' field for PDF viewer, 'content' field for text viewer")
            print(f"   • Both viewers can be tested with Constitutional Law materials")
            
        else:
            print(f"❌ Failed to retrieve materials: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Response: {error_data}")
            except:
                print(f"Response: {response.content}")
            
    except Exception as e:
        print(f"❌ Materials retrieval error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_constitutional_materials()