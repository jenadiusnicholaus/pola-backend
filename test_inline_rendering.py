#!/usr/bin/env python
"""Test template rendering with the new inline format"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/mac/development/python_projects/pola-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from django.template import Template, Context

# Read the template
template_path = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/iii._employment_contract_clean.html'
with open(template_path, 'r', encoding='utf-8') as f:
    template_content = f.read()

# Sample data
context_data = {
    'contract_date_day': '15',
    'contract_date_month': 'January',
    'contract_date_year': '2026',
    'employer_name': 'ABC Company Ltd',
    'employer_address_street': 'Plot 123 Nyerere Road',
    'employer_address_city': 'Dar es Salaam',
    'employer_phone': '+255 22 1234567',
    'employer_email': 'hr@abccompany.co.tz',
    'employee_name': 'John Doe Mwamba',
    'employee_address_street': 'House No. 45 Mwenge',
    'employee_address_city': 'Dar es Salaam',
    'employee_phone': '+255 754 123456',
    'employee_id_type': 'National ID',
    'employee_id_number': '19850312-12345-00012-34',
    'employee_email': 'john.mwamba@email.com',
    'employment_start_day': '1',
    'employment_start_month': 'February',
    'employment_start_year': '2026',
    'employment_end_day': '31',
    'employment_end_month': 'January',
    'employment_end_year': '2028',
    'workplace_location': 'ABC Company Headquarters, Dar es Salaam',
    'work_region': 'Dar es Salaam',
    'work_district': 'Kinondoni',
    'work_ward': 'Mikocheni',
    'job_title': 'Senior Software Developer',
    'job_duties': 'Develop software applications, Lead development team, Review code, Implement best practices',
    'probation_months': '3',
    'work_hours_per_day': '8',
    'work_days_per_week': '5',
    'work_start_time': '08:00',
    'work_end_time': '17:00',
    'salary_amount': '2,500,000',
    'salary_period_month': 'Month',
    'payment_date': '25th',
    'payment_method_bank': 'Bank Transfer',
    'bank_name': 'CRDB Bank',
    'bank_account_name': 'John Doe Mwamba',
    'bank_account_number': '0150123456789',
    'bank_branch': 'Mikocheni Branch',
    'allowance_1': 'Transport Allowance: TZS 200,000',
    'allowance_2': 'Housing Allowance: TZS 500,000',
    'allowance_3': 'Medical Insurance',
    'allowance_4': 'Lunch Allowance: TZS 150,000',
    'other_benefits': 'Annual bonus based on performance, Professional development training'
}

# Render template
template = Template(template_content)
context = Context(context_data)
rendered_html = template.render(context)

# Save rendered HTML
output_path = 'test_inline_rendered.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(rendered_html)

print('✓ Template rendered successfully!')
print(f'✓ Output saved to: {output_path}')
print('\nChecking for formatting:')

# Check if data fields are properly formatted
if '<span class="data-field">' in rendered_html:
    data_field_count = rendered_html.count('<span class="data-field">')
    print(f'✓ Found {data_field_count} data fields with proper formatting')
else:
    print('✗ No data fields found!')

# Check if all variables were replaced
import re
unreplaced = re.findall(r'\{\{[^}]+\}\}', rendered_html)
if unreplaced:
    print(f'\n✗ Unreplaced variables found: {unreplaced[:5]}')  # Show first 5
else:
    print('✓ All variables replaced successfully')

# Check for line breaks after section titles
if '<br/>' in rendered_html:
    br_count = rendered_html.count('<br/>')
    print(f'\nNote: Found {br_count} <br/> tags (should only be in signature section)')
else:
    print('\n✓ No unnecessary line breaks found')

print('\nYou can open test_inline_rendered.html in a browser to preview the formatting.')
