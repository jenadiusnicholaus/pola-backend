#!/usr/bin/env python
"""Seed Employment Contract template fields with sections"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/mac/development/python_projects/pola-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from document_templates.models import DocumentTemplate, TemplateSection, TemplateField

# Get the Employment Contract template
template = DocumentTemplate.objects.get(id=13)

# Clear existing fields and sections for clean slate
template.sections.all().delete()
template.fields.all().delete()

print(f'Seeding fields for: {template.name}')

# Define sections and their fields
sections_data = [
    {
        'name': 'Contract Date',
        'name_sw': 'Tarehe ya Mkataba',
        'order': 1,
        'fields': [
            {'field_name': 'contract_date_day', 'label_en': 'Day', 'label_sw': 'Siku', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min': 1, 'max': 31, 'pattern': '^[0-9]{1,2}$'}},
            {'field_name': 'contract_date_month', 'label_en': 'Month', 'label_sw': 'Mwezi', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 3, 'max_length': 20}},
            {'field_name': 'contract_date_year', 'label_en': 'Year', 'label_sw': 'Mwaka', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min': 2000, 'max': 2100, 'pattern': '^[0-9]{4}$'}},
        ]
    },
    {
        'name': 'Employer Information',
        'name_sw': 'Taarifa za Mwajiri',
        'order': 2,
        'fields': [
            {'field_name': 'employer_name', 'label_en': 'Employer Name', 'label_sw': 'Jina la Mwajiri', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 100}},
            {'field_name': 'employer_address_street', 'label_en': 'Street Address', 'label_sw': 'Anuani ya Mtaa', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 5, 'max_length': 200}},
            {'field_name': 'employer_address_city', 'label_en': 'City', 'label_sw': 'Jiji', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 50}},
            {'field_name': 'employer_phone', 'label_en': 'Phone Number', 'label_sw': 'Namba ya Simu', 'field_type': 'tel', 'is_required': True, 'validation_rules': {'pattern': '^\\+?[0-9\\s\\-]{9,20}$'}},
            {'field_name': 'employer_email', 'label_en': 'Email Address', 'label_sw': 'Barua Pepe', 'field_type': 'email', 'is_required': True, 'validation_rules': {'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'}},
        ]
    },
    {
        'name': 'Employee Information',
        'name_sw': 'Taarifa za Mwajiriwa',
        'order': 3,
        'fields': [
            {'field_name': 'employee_name', 'label_en': 'Employee Name', 'label_sw': 'Jina la Mwajiriwa', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 100}},
            {'field_name': 'employee_address_street', 'label_en': 'Street Address', 'label_sw': 'Anuani ya Mtaa', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 5, 'max_length': 200}},
            {'field_name': 'employee_address_city', 'label_en': 'City', 'label_sw': 'Jiji', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 50}},
            {'field_name': 'employee_phone', 'label_en': 'Phone Number', 'label_sw': 'Namba ya Simu', 'field_type': 'tel', 'is_required': True, 'validation_rules': {'pattern': '^\\+?[0-9\\s\\-]{9,20}$'}},
            {'field_name': 'employee_id_type', 'label_en': 'ID Type', 'label_sw': 'Aina ya Kitambulisho', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 50}},
            {'field_name': 'employee_id_number', 'label_en': 'ID Number', 'label_sw': 'Namba ya Kitambulisho', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 5, 'max_length': 50}},
            {'field_name': 'employee_email', 'label_en': 'Email Address', 'label_sw': 'Barua Pepe', 'field_type': 'email', 'is_required': True, 'validation_rules': {'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'}},
        ]
    },
    {
        'name': 'Employment Period',
        'name_sw': 'Kipindi cha Ajira',
        'order': 4,
        'fields': [
            {'field_name': 'employment_start_day', 'label_en': 'Start Day', 'label_sw': 'Siku ya Kuanza', 'field_type': 'text', 'is_required': True},
            {'field_name': 'employment_start_month', 'label_en': 'Start Month', 'label_sw': 'Mwezi wa Kuanza', 'field_type': 'text', 'is_required': True},
            {'field_name': 'employment_start_year', 'label_en': 'Start Year', 'label_sw': 'Mwaka wa Kuanza', 'field_type': 'text', 'is_required': True},
            {'field_name': 'employment_end_day', 'label_en': 'End Day', 'label_sw': 'Siku ya Mwisho', 'field_type': 'text', 'is_required': False},
            {'field_name': 'employment_end_month', 'label_en': 'End Month', 'label_sw': 'Mwezi wa Mwisho', 'field_type': 'text', 'is_required': False},
            {'field_name': 'employment_end_year', 'label_en': 'End Year', 'label_sw': 'Mwaka wa Mwisho', 'field_type': 'text', 'is_required': False},
        ]
    },
    {
        'name': 'Work Location',
        'name_sw': 'Mahali pa Kazi',
        'order': 5,
        'fields': [
            {'field_name': 'workplace_location', 'label_en': 'Place of Employment', 'label_sw': 'Mahali Alipoajiriwa', 'field_type': 'text', 'is_required': True},
            {'field_name': 'work_region', 'label_en': 'Region', 'label_sw': 'Mkoa', 'field_type': 'text', 'is_required': True},
            {'field_name': 'work_district', 'label_en': 'District', 'label_sw': 'Wilaya', 'field_type': 'text', 'is_required': True},
            {'field_name': 'work_ward', 'label_en': 'Ward', 'label_sw': 'Kata', 'field_type': 'text', 'is_required': True},
        ]
    },
    {
        'name': 'Job Details',
        'name_sw': 'Maelezo ya Kazi',
        'order': 6,
        'fields': [
            {'field_name': 'job_title', 'label_en': 'Job Title/Position', 'label_sw': 'Wadhifa', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 100}},
            {'field_name': 'job_duties', 'label_en': 'Job Duties', 'label_sw': 'Majukumu ya Kazi', 'field_type': 'textarea', 'is_required': True, 'validation_rules': {'min_length': 10, 'max_length': 1000}},
            {'field_name': 'probation_months', 'label_en': 'Probation Period (months)', 'label_sw': 'Muda wa Majaribio (miezi)', 'field_type': 'number', 'is_required': True, 'validation_rules': {'min': 0, 'max': 12}},
        ]
    },
    {
        'name': 'Working Hours',
        'name_sw': 'Muda wa Kazi',
        'order': 7,
        'fields': [
            {'field_name': 'work_hours_per_day', 'label_en': 'Hours per Day', 'label_sw': 'Masaa kwa Siku', 'field_type': 'number', 'is_required': True, 'validation_rules': {'min': 1, 'max': 24}},
            {'field_name': 'work_days_per_week', 'label_en': 'Days per Week', 'label_sw': 'Siku kwa Wiki', 'field_type': 'number', 'is_required': True, 'validation_rules': {'min': 1, 'max': 7}},
            {'field_name': 'work_start_time', 'label_en': 'Start Time', 'label_sw': 'Muda wa Kuanza', 'field_type': 'time', 'is_required': True, 'validation_rules': {'pattern': '^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'}},
            {'field_name': 'work_end_time', 'label_en': 'End Time', 'label_sw': 'Muda wa Kumalizika', 'field_type': 'time', 'is_required': True, 'validation_rules': {'pattern': '^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'}},
        ]
    },
    {
        'name': 'Salary & Payment',
        'name_sw': 'Mshahara na Malipo',
        'order': 8,
        'fields': [
            {'field_name': 'salary_amount', 'label_en': 'Salary Amount', 'label_sw': 'Kiasi cha Mshahara', 'field_type': 'text', 'is_required': True, 'validation_rules': {'pattern': '^[0-9,]+$'}},
            {'field_name': 'salary_period_month', 'label_en': 'Payment Period', 'label_sw': 'Kipindi cha Malipo', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 20}},
            {'field_name': 'payment_date', 'label_en': 'Payment Date', 'label_sw': 'Tarehe ya Malipo', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 1, 'max_length': 10}},
            {'field_name': 'payment_method_bank', 'label_en': 'Payment Method', 'label_sw': 'Njia ya Malipo', 'field_type': 'text', 'is_required': True, 'validation_rules': {'min_length': 2, 'max_length': 50}},
        ]
    },
    {
        'name': 'Bank Details',
        'name_sw': 'Taarifa za Benki',
        'order': 9,
        'fields': [
            {'field_name': 'bank_name', 'label_en': 'Bank Name', 'label_sw': 'Jina la Benki', 'field_type': 'text', 'is_required': False},
            {'field_name': 'bank_account_name', 'label_en': 'Account Name', 'label_sw': 'Jina la Akaunti', 'field_type': 'text', 'is_required': False},
            {'field_name': 'bank_account_number', 'label_en': 'Account Number', 'label_sw': 'Namba ya Akaunti', 'field_type': 'text', 'is_required': False},
            {'field_name': 'bank_branch', 'label_en': 'Branch', 'label_sw': 'Tawi', 'field_type': 'text', 'is_required': False},
        ]
    },
    {
        'name': 'Benefits & Allowances',
        'name_sw': 'Posho na Manufaa',
        'order': 10,
        'fields': [
            {'field_name': 'allowance_1', 'label_en': 'Allowance 1', 'label_sw': 'Posho 1', 'field_type': 'text', 'is_required': False},
            {'field_name': 'allowance_2', 'label_en': 'Allowance 2', 'label_sw': 'Posho 2', 'field_type': 'text', 'is_required': False},
            {'field_name': 'allowance_3', 'label_en': 'Allowance 3', 'label_sw': 'Posho 3', 'field_type': 'text', 'is_required': False},
            {'field_name': 'allowance_4', 'label_en': 'Allowance 4', 'label_sw': 'Posho 4', 'field_type': 'text', 'is_required': False},
            {'field_name': 'other_benefits', 'label_en': 'Other Benefits', 'label_sw': 'Manufaa Mengine', 'field_type': 'textarea', 'is_required': False},
        ]
    },
]

# Create sections and fields
total_fields = 0
for section_data in sections_data:
    # Create section
    section = TemplateSection.objects.create(
        template=template,
        name=section_data['name'],
        name_sw=section_data['name_sw'],
        order=section_data['order']
    )
    print(f'\n✓ Created section: {section.name} ({section.name_sw})')
    
    # Create fields for this section
    for field_data in section_data['fields']:
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
        print(f'  • {field.field_name}: {field.label_en} / {field.label_sw}')
        total_fields += 1

print(f'\n✅ Successfully seeded {total_fields} fields in {len(sections_data)} sections')
print(f'✅ Template: {template.name} (ID: {template.id})')
