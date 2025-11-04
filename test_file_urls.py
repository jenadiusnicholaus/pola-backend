#!/usr/bin/env python
"""Test script to verify file URLs are returned as absolute URLs"""

import os
import django
from django.test import RequestFactory

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from documents.models import LearningMaterial
from subscriptions.serializers import LearningMaterialSerializer

def test_file_urls():
    print("🧪 Testing File URL Serialization")
    print("=" * 50)
    
    # Get a material with a file
    material_with_file = LearningMaterial.objects.filter(file__isnull=False).first()
    
    if not material_with_file:
        print("❌ No materials with files found!")
        return
    
    print(f"📄 Testing material: {material_with_file.title}")
    print(f"📁 File path: {material_with_file.file}")
    
    # Create a mock request for absolute URL generation
    factory = RequestFactory()
    request = factory.get('/test/')
    request.META['HTTP_HOST'] = 'localhost:8000'
    request.META['SERVER_NAME'] = 'localhost'
    request.META['SERVER_PORT'] = '8000'
    
    # Test serializer with request context
    print("\n🔗 Testing with request context:")
    serializer = LearningMaterialSerializer(material_with_file, context={'request': request})
    data = serializer.data
    
    print(f"  File URL: {data.get('file')}")
    print(f"  Is absolute: {'http' in str(data.get('file', ''))}")
    
    # Test serializer without request context (fallback)
    print("\n🔗 Testing without request context (fallback):")
    serializer = LearningMaterialSerializer(material_with_file)
    data = serializer.data
    
    print(f"  File URL: {data.get('file')}")
    print(f"  Is absolute: {'http' in str(data.get('file', ''))}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_file_urls()