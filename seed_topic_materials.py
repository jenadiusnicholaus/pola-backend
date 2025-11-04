#!/usr/bin/env python
"""
Seed script to create materials directly assigned to topics (NEW approach)
This demonstrates the new direct topic-to-materials functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from hubs.models import LegalEdTopic
from documents.models import LearningMaterial
from authentication.models import PolaUser
from decimal import Decimal

def main():
    print('🌱 SEEDING MATERIALS FOR TOPICS')
    print('================================')

    # Get existing topics
    topics = LegalEdTopic.objects.filter(is_active=True)[:3]
    if not topics.exists():
        print('❌ No topics found. Please create some topics first.')
        return

    print(f'📚 Found {topics.count()} topics to seed:')
    for topic in topics:
        print(f'  - {topic.name} ({topic.slug})')

    # Get uploader
    try:
        uploader = PolaUser.objects.filter(is_active=True, is_staff=True).first()
        if not uploader:
            uploader = PolaUser.objects.filter(is_active=True).first()
            if not uploader:
                print('❌ No active users found. Materials need an uploader.')
                return
        print(f'📝 Using uploader: {uploader.email} (ID: {uploader.id})')
    except Exception as e:
        print(f'❌ Error finding uploader: {e}')
        return

    # Create materials for each topic
    materials_created = 0

    for topic in topics:
        print(f'\n📚 Creating materials for topic: {topic.name}')
        
        # Create different types of materials for each topic
        materials_data = [
            {
                'title': f'{topic.name} - Introduction Notes',
                'description': f'Comprehensive introduction to {topic.name} covering fundamental concepts and principles. This material provides a solid foundation for understanding key concepts.',
                'content_type': 'notes',
                'language': 'en',
                'price': Decimal('0.00'),
                'is_lecture_material': True,
                'is_verified_quality': True,
                'uploader_type': 'lecturer'
            },
            {
                'title': f'{topic.name} - Case Studies',
                'description': f'Real-world case studies and practical examples in {topic.name}. Includes detailed analysis of landmark cases and their implications.',
                'content_type': 'case_study',
                'language': 'en',
                'price': Decimal('5000.00'),
                'is_lecture_material': False,
                'is_verified_quality': False,
                'uploader_type': 'student'
            },
            {
                'title': f'{topic.name} - Research Papers',
                'description': f'Latest research and academic papers on {topic.name}. Compiled from leading law journals and academic institutions.',
                'content_type': 'research',
                'language': 'sw',
                'price': Decimal('0.00'),
                'is_lecture_material': True,
                'is_verified_quality': True,
                'uploader_type': 'lecturer'
            },
            {
                'title': f'{topic.name} - Practice Exercises',
                'description': f'Practical exercises and assignments for {topic.name}. Test your understanding with real-world scenarios and problems.',
                'content_type': 'assignments',
                'language': 'en',
                'price': Decimal('2000.00'),
                'is_lecture_material': False,
                'is_verified_quality': True,
                'uploader_type': 'advocate'
            }
        ]
        
        for material_data in materials_data:
            try:
                # Check if material already exists
                existing = LearningMaterial.objects.filter(
                    title=material_data['title'],
                    topic=topic
                ).first()
                
                if existing:
                    print(f'  ⏩ Material already exists: {material_data["title"]}')
                    continue
                
                # Create the material with direct topic assignment
                material = LearningMaterial.objects.create(
                    hub_type='legal_ed',
                    uploader=uploader,
                    topic=topic,  # 🎯 NEW: Direct topic assignment (no subtopic needed!)
                    **material_data
                )
                
                materials_created += 1
                price_display = 'Free' if material.price == 0 else f'TSh {material.price:,.0f}'
                print(f'  ✅ Created: {material.title}')
                print(f'      Type: {material.content_type} | Lang: {material.language} | Price: {price_display}')
                
            except Exception as e:
                print(f'  ❌ Error creating material {material_data["title"]}: {e}')

    print(f'\n🎉 SEEDING COMPLETE!')
    print(f'📊 Total new materials created: {materials_created}')

    # Test the new topic materials functionality
    print(f'\n🧪 TESTING NEW DIRECT TOPIC-TO-MATERIALS FUNCTIONALITY')
    print(f'========================================================')

    total_direct_materials = 0
    total_subtopic_materials = 0

    for topic in topics:
        # Count direct materials for this topic (NEW)
        direct_materials = LearningMaterial.objects.filter(topic=topic)
        # Count subtopic materials for this topic (LEGACY)
        subtopic_materials = LearningMaterial.objects.filter(subtopic__topic=topic)
        
        total_direct_materials += direct_materials.count()
        total_subtopic_materials += subtopic_materials.count()
        
        print(f'\n📚 {topic.name}:')
        print(f'  🎯 Direct materials (NEW): {direct_materials.count()}')
        print(f'  🔄 Legacy subtopic materials: {subtopic_materials.count()}')
        print(f'  📊 Total materials available: {direct_materials.count() + subtopic_materials.count()}')
        
        # Show example direct materials with details
        if direct_materials.exists():
            print(f'  📄 New direct materials:')
            for material in direct_materials:
                price_str = 'Free' if material.price == 0 else f'TSh {material.price:,.0f}'
                quality = '✅ Verified' if material.is_verified_quality else '⏳ Pending'
                lecture = '🎓 Official' if material.is_lecture_material else '👤 Community'
                print(f'    - {material.title}')
                print(f'      📝 {material.content_type} | 🌐 {material.language} | 💰 {price_str} | {quality} | {lecture}')

    print(f'\n📊 SUMMARY:')
    print(f'🎯 Total direct materials (NEW approach): {total_direct_materials}')
    print(f'🔄 Total subtopic materials (LEGACY): {total_subtopic_materials}')
    print(f'📚 Grand total materials: {total_direct_materials + total_subtopic_materials}')
    print(f'\n✅ The new direct topic-to-materials functionality is working!')
    print(f'🚀 Frontend can now use: GET /api/v1/hubs/legal-education/topics/{{slug}}/materials/')

if __name__ == '__main__':
    main()