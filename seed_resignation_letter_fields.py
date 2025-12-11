"""
Seed script for Resignation Letter template fields
Creates a new template with bilingual support and all fields with validation rules
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from document_templates.models import DocumentTemplate, TemplateSection, TemplateField

# Read template files
with open('document_templates/templates/resignation_letter_en.html', 'r') as f:
    template_content_en = f.read()

with open('document_templates/templates/resignation_letter_sw.html', 'r') as f:
    template_content_sw = f.read()

# Create or update the Resignation Letter template
template, created = DocumentTemplate.objects.update_or_create(
    name='Resignation Letter',
    defaults={
        'name_sw': 'Barua ya Kujiuzulu',
        'description': 'Professional resignation letter for employees leaving their position',
        'description_sw': 'Barua rasmi ya kujiuzulu kwa wafanyakazi wanaoondoka kazini',
        'category': 'resignation',
        'template_content_en': template_content_en,
        'template_content_sw': template_content_sw,
        'is_free': True,
        'price': 0.00,
        'icon': '📝',
        'order': 2,
        'is_active': True
    }
)

print(f"\n{'Created' if created else 'Updated'} template: {template.name}")
print(f"Template ID: {template.id}")

# Clear existing sections and fields for this template
TemplateSection.objects.filter(template=template).delete()

# Define sections with fields and validation rules
sections_data = [
    {
        'name': 'Employee Information',
        'name_sw': 'Taarifa za Mwajiriwa',
        'description': 'Information about the resigning employee',
        'description_sw': 'Taarifa kuhusu mwajiriwa anayejiuzulu',
        'order': 1,
        'fields': [
            {
                'field_name': 'employee_name',
                'label_en': 'Employee Full Name',
                'label_sw': 'Jina Kamili la Mwajiriwa',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 2, 'max_length': 100}
            },
            {
                'field_name': 'employee_po_box',
                'label_en': 'P.O Box',
                'label_sw': 'S.L.P',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 1, 'max_length': 20}
            },
            {
                'field_name': 'employee_city',
                'label_en': 'City',
                'label_sw': 'Jiji',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 2, 'max_length': 50}
            },
            {
                'field_name': 'employee_phone',
                'label_en': 'Phone Number',
                'label_sw': 'Namba ya Simu',
                'field_type': 'tel',
                'is_required': True,
                'validation_rules': {'pattern': r'^\+?[0-9\s\-]{9,20}$'}
            },
            {
                'field_name': 'employee_email',
                'label_en': 'Email Address',
                'label_sw': 'Barua Pepe',
                'field_type': 'email',
                'is_required': True,
                'validation_rules': {'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'}
            }
        ]
    },
    {
        'name': 'Letter Date',
        'name_sw': 'Tarehe ya Barua',
        'description': 'Date when the letter is written',
        'description_sw': 'Tarehe ya kuandikwa kwa barua',
        'order': 2,
        'fields': [
            {
                'field_name': 'letter_date_day',
                'label_en': 'Day',
                'label_sw': 'Siku',
                'field_type': 'number',
                'is_required': True,
                'validation_rules': {'min': 1, 'max': 31, 'pattern': r'^[0-9]{1,2}$'}
            },
            {
                'field_name': 'letter_date_month',
                'label_en': 'Month',
                'label_sw': 'Mwezi',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 3, 'max_length': 20}
            },
            {
                'field_name': 'letter_date_year',
                'label_en': 'Year',
                'label_sw': 'Mwaka',
                'field_type': 'number',
                'is_required': True,
                'validation_rules': {'min': 2000, 'max': 2100, 'pattern': r'^[0-9]{4}$'}
            }
        ]
    },
    {
        'name': 'Employer Information',
        'name_sw': 'Taarifa za Mwajiri',
        'description': 'Information about the employer/organization',
        'description_sw': 'Taarifa kuhusu mwajiri/shirika',
        'order': 3,
        'fields': [
            {
                'field_name': 'employer_name',
                'label_en': 'Employer/Recipient Name',
                'label_sw': 'Jina la Mwajiri/Mpokeaji',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 2, 'max_length': 100}
            },
            {
                'field_name': 'employer_po_box',
                'label_en': 'P.O Box',
                'label_sw': 'S.L.P',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 1, 'max_length': 20}
            },
            {
                'field_name': 'employer_city',
                'label_en': 'City',
                'label_sw': 'Jiji',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 2, 'max_length': 50}
            }
        ]
    },
    {
        'name': 'Position Details',
        'name_sw': 'Maelezo ya Nafasi',
        'description': 'Details about the position being resigned from',
        'description_sw': 'Maelezo kuhusu nafasi inayoachwa',
        'order': 4,
        'fields': [
            {
                'field_name': 'job_title',
                'label_en': 'Job Title/Position',
                'label_sw': 'Cheo/Nafasi',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 2, 'max_length': 100}
            },
            {
                'field_name': 'organization_name',
                'label_en': 'Organization/Company Name',
                'label_sw': 'Jina la Shirika/Kampuni',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 2, 'max_length': 150}
            }
        ]
    },
    {
        'name': 'Resignation Details',
        'name_sw': 'Maelezo ya Kujiuzulu',
        'description': 'Details about the resignation',
        'description_sw': 'Maelezo kuhusu uamuzi wa kujiuzulu',
        'order': 5,
        'fields': [
            {
                'field_name': 'resignation_date_day',
                'label_en': 'Effective Day',
                'label_sw': 'Siku ya Kuanza',
                'field_type': 'number',
                'is_required': True,
                'validation_rules': {'min': 1, 'max': 31, 'pattern': r'^[0-9]{1,2}$'}
            },
            {
                'field_name': 'resignation_date_month',
                'label_en': 'Effective Month',
                'label_sw': 'Mwezi wa Kuanza',
                'field_type': 'text',
                'is_required': True,
                'validation_rules': {'min_length': 3, 'max_length': 20}
            },
            {
                'field_name': 'resignation_date_year',
                'label_en': 'Effective Year',
                'label_sw': 'Mwaka wa Kuanza',
                'field_type': 'number',
                'is_required': True,
                'validation_rules': {'min': 2000, 'max': 2100, 'pattern': r'^[0-9]{4}$'}
            },
            {
                'field_name': 'resignation_reason',
                'label_en': 'Reason for Resignation',
                'label_sw': 'Sababu ya Kujiuzulu',
                'field_type': 'textarea',
                'is_required': True,
                'validation_rules': {'min_length': 10, 'max_length': 500}
            }
        ]
    }
]

# Create sections and fields
print(f"\nSeeding fields for: {template.name}\n")

total_fields = 0
for section_data in sections_data:
    # Extract fields from section data
    fields_data = section_data.pop('fields')
    
    # Create section
    section = TemplateSection.objects.create(
        template=template,
        **section_data
    )
    
    print(f"✓ Created section: {section.name} ({section.name_sw})")
    
    # Create fields for this section
    for field_data in fields_data:
        field = TemplateField.objects.create(
            template=template,
            section=section,
            field_name=field_data['field_name'],
            label_en=field_data['label_en'],
            label_sw=field_data['label_sw'],
            field_type=field_data['field_type'],
            is_required=field_data['is_required'],
            validation_rules=field_data.get('validation_rules', {}),
            order=total_fields + 1
        )
        print(f"  • {field.field_name}: {field.label_en} / {field.label_sw}")
        total_fields += 1

print(f"\n✅ Successfully seeded {total_fields} fields in {len(sections_data)} sections")
print(f"✅ Template: {template.name} (ID: {template.id})")
