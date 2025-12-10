#!/usr/bin/env python
"""
Test document generation with actual template
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/mac/development/python_projects/pola-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from document_templates.models import DocumentTemplate
from document_templates.utils.pdf_generator import PDFGenerator
from django.conf import settings

print("="*70)
print("TESTING DOCUMENT GENERATION")
print("="*70)

# Get a template
try:
    template = DocumentTemplate.objects.first()
    if not template:
        print("❌ No templates found. Run: python manage.py seed_templates")
        sys.exit(1)
    
    print(f"\n✅ Template: {template.name} ({template.name_sw})")
    print(f"   Fields: {template.fields.count()}")
    print(f"   Category: {template.category}")
    
    # Create sample data
    sample_data = {}
    for field in template.fields.all():
        field_name = field.field_name
        if 'name' in field_name.lower():
            sample_data[field_name] = "Test Name"
        elif 'date' in field_name.lower():
            sample_data[field_name] = "2025-12-09"
        elif 'email' in field_name.lower():
            sample_data[field_name] = "test@example.com"
        elif 'phone' in field_name.lower():
            sample_data[field_name] = "+255 712 345 678"
        elif 'address' in field_name.lower():
            sample_data[field_name] = "123 Test Street, Dar es Salaam"
        elif 'position' in field_name.lower() or 'nafasi' in field_name.lower():
            sample_data[field_name] = "Software Engineer"
        elif 'department' in field_name.lower() or 'idara' in field_name.lower():
            sample_data[field_name] = "IT Department"
        elif 'salary' in field_name.lower() or 'mshahara' in field_name.lower():
            sample_data[field_name] = "2000000"
        elif 'period' in field_name.lower() or 'kipindi' in field_name.lower():
            sample_data[field_name] = "30 days"
        elif 'leave' in field_name.lower() or 'likizo' in field_name.lower():
            sample_data[field_name] = "28"
        elif 'hours' in field_name.lower() or 'masaa' in field_name.lower():
            sample_data[field_name] = "40 hours per week"
        else:
            sample_data[field_name] = f"Sample {field.label_en}"
    
    print(f"\n✅ Created sample data for {len(sample_data)} fields")
    
    # Generate PDF
    print("\n🔄 Generating PDF...")
    pdf_generator = PDFGenerator()
    
    output_dir = os.path.join(settings.MEDIA_ROOT, 'generated_documents', 'test')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'test_document.pdf')
    
    pdf_path = pdf_generator.generate_document(
        template.template_content_en,
        sample_data,
        output_path
    )
    
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"✅ PDF generated successfully!")
        print(f"   File: {pdf_path}")
        print(f"   Size: {size:,} bytes")
    else:
        print(f"❌ PDF file not found at: {pdf_path}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
