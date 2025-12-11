import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from document_templates.models import DocumentTemplate, TemplateField, TemplateSection

# Get or create the Notice template
template, created = DocumentTemplate.objects.get_or_create(
    name='Notice of Termination',
    defaults={
        'name_sw': 'Taarifa ya Kusitisha Ajira',
        'description': 'Formal notice of employment termination from employer to employee',
        'description_sw': 'Taarifa rasmi ya kusitisha ajira kutoka kwa mwajiri kwa mfanyakazi',
        'category': 'legal_notice',
        'template_content_en': 'notice_en.html',
        'template_content_sw': 'notice_sw.html',
    }
)

if created:
    print(f"✅ Created Notice template with ID: {template.id}")
else:
    print(f"ℹ️  Notice template already exists with ID: {template.id}")

# Define sections with fields
sections_data = [
    {
        "section_name_en": "Employer Information",
        "section_name_sw": "Taarifa za Mwajiri",
        "order": 1,
        "fields": [
            {
                "field_name": "employer_name",
                "label_en": "Employer Name",
                "label_sw": "Jina la Mwajiri",
                "field_type": "text",
                "is_required": True,
                "order": 1,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "2"},
                    {"rule_type": "max_length", "rule_value": "200"}
                ]
            },
            {
                "field_name": "employer_po_box",
                "label_en": "P.O. Box",
                "label_sw": "S.L.P",
                "field_type": "text",
                "is_required": True,
                "order": 2,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "1"},
                    {"rule_type": "max_length", "rule_value": "50"}
                ]
            },
            {
                "field_name": "employer_city",
                "label_en": "City",
                "label_sw": "Mji",
                "field_type": "text",
                "is_required": True,
                "order": 3,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "2"},
                    {"rule_type": "max_length", "rule_value": "100"}
                ]
            },
            {
                "field_name": "employer_phone",
                "label_en": "Phone",
                "label_sw": "Simu",
                "field_type": "text",
                "is_required": True,
                "order": 4,
                "validations": [
                    {"rule_type": "pattern", "rule_value": "^\\+?[0-9\\s\\-()]{7,20}$"}
                ]
            },
            {
                "field_name": "employer_email",
                "label_en": "Email",
                "label_sw": "Barua Pepe",
                "field_type": "email",
                "is_required": True,
                "order": 5,
                "validations": [
                    {"rule_type": "pattern", "rule_value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
                ]
            },
            {
                "field_name": "notice_date_day",
                "label_en": "Day",
                "label_sw": "Siku",
                "field_type": "text",
                "is_required": True,
                "order": 6,
                "validations": [
                    {"rule_type": "min", "rule_value": "1"},
                    {"rule_type": "max", "rule_value": "31"}
                ]
            },
            {
                "field_name": "notice_date_month",
                "label_en": "Month",
                "label_sw": "Mwezi",
                "field_type": "text",
                "is_required": True,
                "order": 7,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "3"},
                    {"rule_type": "max_length", "rule_value": "20"}
                ]
            },
            {
                "field_name": "notice_date_year",
                "label_en": "Year",
                "label_sw": "Mwaka",
                "field_type": "text",
                "is_required": True,
                "order": 8,
                "validations": [
                    {"rule_type": "min", "rule_value": "2000"},
                    {"rule_type": "max", "rule_value": "2100"}
                ]
            }
        ]
    },
    {
        "section_name_en": "Employee Information",
        "section_name_sw": "Taarifa za Mfanyakazi",
        "order": 2,
        "fields": [
            {
                "field_name": "employee_name",
                "label_en": "Employee Name",
                "label_sw": "Jina la Mfanyakazi",
                "field_type": "text",
                "is_required": True,
                "order": 1,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "2"},
                    {"rule_type": "max_length", "rule_value": "200"}
                ]
            },
            {
                "field_name": "employee_po_box",
                "label_en": "P.O. Box",
                "label_sw": "S.L.P",
                "field_type": "text",
                "is_required": True,
                "order": 2,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "1"},
                    {"rule_type": "max_length", "rule_value": "50"}
                ]
            },
            {
                "field_name": "employee_city",
                "label_en": "City",
                "label_sw": "Mji",
                "field_type": "text",
                "is_required": True,
                "order": 3,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "2"},
                    {"rule_type": "max_length", "rule_value": "100"}
                ]
            }
        ]
    },
    {
        "section_name_en": "Termination Details",
        "section_name_sw": "Maelezo ya Kusitisha Ajira",
        "order": 3,
        "fields": [
            {
                "field_name": "contract_date",
                "label_en": "Contract Date",
                "label_sw": "Tarehe ya Mkataba",
                "field_type": "text",
                "is_required": True,
                "order": 1,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "5"},
                    {"rule_type": "max_length", "rule_value": "50"}
                ]
            },
            {
                "field_name": "termination_date",
                "label_en": "Termination Date",
                "label_sw": "Tarehe ya Kusitisha",
                "field_type": "text",
                "is_required": True,
                "order": 2,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "5"},
                    {"rule_type": "max_length", "rule_value": "50"}
                ]
            },
            {
                "field_name": "termination_reasons",
                "label_en": "Termination Reasons",
                "label_sw": "Sababu za Kusitisha",
                "field_type": "textarea",
                "is_required": True,
                "order": 3,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "10"},
                    {"rule_type": "max_length", "rule_value": "1000"}
                ]
            },
            {
                "field_name": "notice_period_days",
                "label_en": "Notice Period (Days)",
                "label_sw": "Kipindi cha Taarifa (Siku)",
                "field_type": "number",
                "is_required": True,
                "order": 4,
                "validations": [
                    {"rule_type": "min", "rule_value": "1"},
                    {"rule_type": "max", "rule_value": "365"}
                ]
            }
        ]
    },
    {
        "section_name_en": "Signature Information",
        "section_name_sw": "Taarifa za Sahihi",
        "order": 4,
        "fields": [
            {
                "field_name": "representative_name",
                "label_en": "Representative Name",
                "label_sw": "Jina la Mwakilishi",
                "field_type": "text",
                "is_required": True,
                "order": 1,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "2"},
                    {"rule_type": "max_length", "rule_value": "200"}
                ]
            },
            {
                "field_name": "representative_position",
                "label_en": "Position",
                "label_sw": "Nafasi",
                "field_type": "text",
                "is_required": True,
                "order": 2,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "2"},
                    {"rule_type": "max_length", "rule_value": "100"}
                ]
            },
            {
                "field_name": "signature_date",
                "label_en": "Signature Date",
                "label_sw": "Tarehe ya Sahihi",
                "field_type": "text",
                "is_required": True,
                "order": 3,
                "validations": [
                    {"rule_type": "min_length", "rule_value": "5"},
                    {"rule_type": "max_length", "rule_value": "50"}
                ]
            }
        ]
    }
]

# Create sections and fields
total_fields = 0
for section_data in sections_data:
    # Get or create section
    section, section_created = TemplateSection.objects.get_or_create(
        template=template,
        name=section_data['section_name_en'],
        defaults={
            'name_sw': section_data['section_name_sw'],
            'order': section_data['order']
        }
    )
    
    if section_created:
        print(f"  ✅ Created section: {section_data['section_name_en']}")
    else:
        print(f"  ℹ️  Section already exists: {section_data['section_name_en']}")
    
    # Create fields for this section
    for field_data in section_data['fields']:
        # Build validation_rules dict
        validation_rules = {}
        for validation in field_data.get('validations', []):
            validation_rules[validation['rule_type']] = validation['rule_value']
        
        field, field_created = TemplateField.objects.get_or_create(
            template=template,
            field_name=field_data['field_name'],
            defaults={
                'label_en': field_data['label_en'],
                'label_sw': field_data['label_sw'],
                'field_type': field_data['field_type'],
                'is_required': field_data['is_required'],
                'order': (section_data['order'] * 100) + field_data['order'],
                'section': section,
                'validation_rules': validation_rules
            }
        )
        
        if field_created:
            total_fields += 1
            print(f"    ✅ Created field: {field_data['field_name']}")
        else:
            print(f"    ℹ️  Field already exists: {field_data['field_name']}")

print(f"\n✅ Notice template seeding complete!")
print(f"   Template ID: {template.id}")
print(f"   Total sections: {len(sections_data)}")
print(f"   Total fields: {total_fields if total_fields > 0 else 'Already existed'}")
