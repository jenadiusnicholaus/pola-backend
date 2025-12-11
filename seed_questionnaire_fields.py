import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from document_templates.models import DocumentTemplate, TemplateField, TemplateSection

# Get or create the Questionnaire template
template, created = DocumentTemplate.objects.get_or_create(
    name='Employment Questionnaire',
    defaults={
        'name_sw': 'Dodoso la Ajira',
        'description': 'Comprehensive employment questionnaire form for contract creation',
        'description_sw': 'Fomu kamili ya dodoso la ajira kwa kutengeneza mkataba',
        'category': 'questionnaire',
        'template_content_en': 'questionnaire_en.html',
        'template_content_sw': 'questionnaire_sw.html',
    }
)

if created:
    print(f"✅ Created Questionnaire template with ID: {template.id}")
else:
    print(f"ℹ️  Questionnaire template already exists with ID: {template.id}")

# Define sections with fields
sections_data = [
    {
        "section_name_en": "Date of Contract Creation",
        "section_name_sw": "Tarehe ya Kutengeneza Mkataba",
        "order": 1,
        "fields": [
            {"field_name": "contract_date_day", "label_en": "Day", "label_sw": "Tarehe", "field_type": "text", "order": 1, "validations": [{"rule_type": "min", "rule_value": "1"}, {"rule_type": "max", "rule_value": "31"}]},
            {"field_name": "contract_date_month", "label_en": "Month", "label_sw": "Mwezi", "field_type": "text", "order": 2, "validations": [{"rule_type": "min_length", "rule_value": "3"}, {"rule_type": "max_length", "rule_value": "20"}]},
            {"field_name": "contract_date_year", "label_en": "Year", "label_sw": "Mwaka", "field_type": "text", "order": 3, "validations": [{"rule_type": "min", "rule_value": "2000"}, {"rule_type": "max", "rule_value": "2100"}]},
        ]
    },
    {
        "section_name_en": "Employer Information",
        "section_name_sw": "Taarifa za Mwajiri",
        "order": 2,
        "fields": [
            {"field_name": "employer_name", "label_en": "Full name of Employer", "label_sw": "Jina kamili la Mwajiri", "field_type": "text", "order": 1, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "employer_po_box", "label_en": "P.O. Box", "label_sw": "S.L.P", "field_type": "text", "order": 2, "validations": [{"rule_type": "min_length", "rule_value": "1"}, {"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "employer_region", "label_en": "Region", "label_sw": "Mkoa", "field_type": "text", "order": 3, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "employer_phone", "label_en": "Phone Number", "label_sw": "Namba ya Simu", "field_type": "text", "order": 4, "validations": [{"rule_type": "pattern", "rule_value": "^\\+?[0-9\\s\\-()]{7,20}$"}]},
            {"field_name": "employer_email", "label_en": "Email", "label_sw": "Barua Pepe", "field_type": "email", "order": 5, "validations": [{"rule_type": "pattern", "rule_value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}]},
        ]
    },
    {
        "section_name_en": "Employee Information",
        "section_name_sw": "Taarifa za Mwajiriwa",
        "order": 3,
        "fields": [
            {"field_name": "employee_name", "label_en": "Full name of Employee", "label_sw": "Jina kamili la Mwajiriwa", "field_type": "text", "order": 1, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "employee_po_box", "label_en": "P.O. Box", "label_sw": "S.L.P", "field_type": "text", "order": 2, "validations": [{"rule_type": "min_length", "rule_value": "1"}, {"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "employee_region", "label_en": "Region", "label_sw": "Mkoa", "field_type": "text", "order": 3, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "employee_phone", "label_en": "Phone Number", "label_sw": "Namba ya Simu", "field_type": "text", "order": 4, "validations": [{"rule_type": "pattern", "rule_value": "^\\+?[0-9\\s\\-()]{7,20}$"}]},
            {"field_name": "employee_id_type", "label_en": "Identification Type", "label_sw": "Aina ya Kitambulisho", "field_type": "text", "order": 5, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "employee_id_number", "label_en": "Identification Number", "label_sw": "Namba ya Kitambulisho", "field_type": "text", "order": 6, "validations": [{"rule_type": "min_length", "rule_value": "5"}, {"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "employee_email", "label_en": "Email", "label_sw": "Barua Pepe", "field_type": "email", "order": 7, "validations": [{"rule_type": "pattern", "rule_value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}]},
        ]
    },
    {
        "section_name_en": "Date of Commencement of Employment",
        "section_name_sw": "Tarehe ya Kuanza Kazi",
        "order": 4,
        "fields": [
            {"field_name": "start_date_day", "label_en": "Start Day", "label_sw": "Siku ya Kuanza", "field_type": "text", "order": 1, "validations": [{"rule_type": "min", "rule_value": "1"}, {"rule_type": "max", "rule_value": "31"}]},
            {"field_name": "start_date_month", "label_en": "Start Month", "label_sw": "Mwezi wa Kuanza", "field_type": "text", "order": 2, "validations": [{"rule_type": "min_length", "rule_value": "3"}, {"rule_type": "max_length", "rule_value": "20"}]},
            {"field_name": "start_date_year", "label_en": "Start Year", "label_sw": "Mwaka wa Kuanza", "field_type": "text", "order": 3, "validations": [{"rule_type": "min", "rule_value": "2000"}, {"rule_type": "max", "rule_value": "2100"}]},
            {"field_name": "end_date_day", "label_en": "End Day", "label_sw": "Siku ya Mwisho", "field_type": "text", "order": 4, "validations": []},
            {"field_name": "end_date_month", "label_en": "End Month", "label_sw": "Mwezi wa Mwisho", "field_type": "text", "order": 5, "validations": []},
            {"field_name": "end_date_year", "label_en": "End Year", "label_sw": "Mwaka wa Mwisho", "field_type": "text", "order": 6, "validations": []},
        ]
    },
    {
        "section_name_en": "Place of Employment",
        "section_name_sw": "Mahali Alipoajiriwa",
        "order": 5,
        "fields": [
            {"field_name": "employment_region", "label_en": "Region of employment", "label_sw": "Mkoa alipoajiriwa", "field_type": "text", "order": 1, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "work_location_region", "label_en": "Work Location Region", "label_sw": "Mkoa wa Eneo la Kazi", "field_type": "text", "order": 2, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "work_location_district", "label_en": "District", "label_sw": "Wilaya", "field_type": "text", "order": 3, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "work_location_ward", "label_en": "Ward", "label_sw": "Kata", "field_type": "text", "order": 4, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
        ]
    },
    {
        "section_name_en": "Position / Job Description",
        "section_name_sw": "Wadhifa / Kazi ya Kufanya",
        "order": 6,
        "fields": [
            {"field_name": "job_title", "label_en": "Job title/position", "label_sw": "Cheo/nafasi ya kazi", "field_type": "text", "order": 1, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_1", "label_en": "Duty 1", "label_sw": "Jukumu 1", "field_type": "text", "order": 2, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_2", "label_en": "Duty 2", "label_sw": "Jukumu 2", "field_type": "text", "order": 3, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_3", "label_en": "Duty 3", "label_sw": "Jukumu 3", "field_type": "text", "order": 4, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_4", "label_en": "Duty 4", "label_sw": "Jukumu 4", "field_type": "text", "order": 5, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_5", "label_en": "Duty 5", "label_sw": "Jukumu 5", "field_type": "text", "order": 6, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_6", "label_en": "Duty 6", "label_sw": "Jukumu 6", "field_type": "text", "order": 7, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_7", "label_en": "Duty 7", "label_sw": "Jukumu 7", "field_type": "text", "order": 8, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_8", "label_en": "Duty 8", "label_sw": "Jukumu 8", "field_type": "text", "order": 9, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_9", "label_en": "Duty 9", "label_sw": "Jukumu 9", "field_type": "text", "order": 10, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "duty_10", "label_en": "Duty 10", "label_sw": "Jukumu 10", "field_type": "text", "order": 11, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
        ]
    },
    {
        "section_name_en": "Probation Period",
        "section_name_sw": "Muda wa Majaribio",
        "order": 7,
        "fields": [
            {"field_name": "probation_period", "label_en": "Duration of probation period", "label_sw": "Muda wa kipindi cha majaribio", "field_type": "text", "order": 1, "validations": [{"rule_type": "min_length", "rule_value": "1"}, {"rule_type": "max_length", "rule_value": "50"}]},
        ]
    },
    {
        "section_name_en": "Working Hours",
        "section_name_sw": "Muda wa Kazi",
        "order": 8,
        "fields": [
            {"field_name": "working_hours_per_day", "label_en": "Working hours per day", "label_sw": "Masaa ya kazi kwa siku", "field_type": "number", "order": 1, "validations": [{"rule_type": "min", "rule_value": "1"}, {"rule_type": "max", "rule_value": "24"}]},
            {"field_name": "working_days_per_week", "label_en": "Working days per week", "label_sw": "Siku za kazi kwa wiki", "field_type": "number", "order": 2, "validations": [{"rule_type": "min", "rule_value": "1"}, {"rule_type": "max", "rule_value": "7"}]},
            {"field_name": "work_time_from", "label_en": "Work time from", "label_sw": "Muda wa kazi kuanzia", "field_type": "text", "order": 3, "validations": [{"rule_type": "min_length", "rule_value": "1"}, {"rule_type": "max_length", "rule_value": "20"}]},
            {"field_name": "work_time_to", "label_en": "Work time to", "label_sw": "Muda wa kazi hadi", "field_type": "text", "order": 4, "validations": [{"rule_type": "min_length", "rule_value": "1"}, {"rule_type": "max_length", "rule_value": "20"}]},
        ]
    },
    {
        "section_name_en": "Salary and Payment",
        "section_name_sw": "Mshahara na Malipo",
        "order": 9,
        "fields": [
            {"field_name": "salary_amount", "label_en": "Amount of salary", "label_sw": "Kiasi cha mshahara", "field_type": "text", "order": 1, "validations": [{"rule_type": "min_length", "rule_value": "1"}, {"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "payment_period", "label_en": "Payment period", "label_sw": "Kipindi cha malipo", "field_type": "text", "order": 2, "validations": [{"rule_type": "min_length", "rule_value": "3"}, {"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "payment_date", "label_en": "Payment date if monthly", "label_sw": "Tarehe ya malipo kwa mwezi", "field_type": "text", "order": 3, "validations": [{"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "payment_mode", "label_en": "Mode of payment", "label_sw": "Njia ya malipo", "field_type": "text", "order": 4, "validations": [{"rule_type": "min_length", "rule_value": "2"}, {"rule_type": "max_length", "rule_value": "100"}]},
            {"field_name": "bank_name", "label_en": "Bank Name", "label_sw": "Jina la Benki", "field_type": "text", "order": 5, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "bank_branch", "label_en": "Bank Branch", "label_sw": "Tawi la Benki", "field_type": "text", "order": 6, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "account_name", "label_en": "Account Name", "label_sw": "Jina la Akaunti", "field_type": "text", "order": 7, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
            {"field_name": "account_number", "label_en": "Account Number", "label_sw": "Namba ya Akaunti", "field_type": "text", "order": 8, "validations": [{"rule_type": "max_length", "rule_value": "50"}]},
        ]
    },
    {
        "section_name_en": "Allowances and Benefits",
        "section_name_sw": "Posho na Manufaa",
        "order": 10,
        "fields": [
            {"field_name": "transport_allowance", "label_en": "Transport allowance", "label_sw": "Posho ya usafiri", "field_type": "text", "order": 1, "validations": [{"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "meal_allowance", "label_en": "Meal allowance", "label_sw": "Posho ya chakula", "field_type": "text", "order": 2, "validations": [{"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "accommodation_allowance", "label_en": "Accommodation", "label_sw": "Malazi", "field_type": "text", "order": 3, "validations": [{"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "health_insurance", "label_en": "Health insurance", "label_sw": "Bima ya afya", "field_type": "text", "order": 4, "validations": [{"rule_type": "max_length", "rule_value": "50"}]},
            {"field_name": "other_benefits", "label_en": "Other benefits", "label_sw": "Manufaa mengine", "field_type": "text", "order": 5, "validations": [{"rule_type": "max_length", "rule_value": "200"}]},
        ]
    },
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
                'is_required': field_data.get('is_required', True),
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

print(f"\n✅ Questionnaire template seeding complete!")
print(f"   Template ID: {template.id}")
print(f"   Total sections: {len(sections_data)}")
print(f"   Total fields: {total_fields if total_fields > 0 else 'Already existed'}")
