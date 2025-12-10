#!/usr/bin/env python
"""Convert Swahili Employment Contract template placeholders to Django template variables"""

# Field mapping for Swahili Employment Contract (Mkataba wa Ajira)
# Using the same variable names as English version for consistency

field_mapping = {
    # Contract dates
    '1(a)': '{{contract_date_day}}',
    '1(b)': '{{contract_date_month}}',
    '1(c)': '{{contract_date_year}}',
    
    # Employer (Mwajiri) details
    '2(a)': '{{employer_name}}',
    '2(b)(i)': '{{employer_address_street}}',
    '2(b)(ii)': '{{employer_address_city}}',
    '2(c)': '{{employer_phone}}',
    '2(d)': '{{employer_email}}',
    
    # Employee (Mwajiriwa) details
    '3(a)': '{{employee_name}}',
    '3(b)(i)': '{{employee_address_street}}',
    '3(b)(ii)': '{{employee_address_city}}',
    '3(c)': '{{employee_phone}}',
    '3(d)': '{{employee_id_type}}',
    '3(e)': '{{employee_id_number}}',
    '3(f)': '{{employee_email}}',
    
    # Employment start date
    '4(a)(i)': '{{employment_start_day}}',
    '4(a)(ii)': '{{employment_start_month}}',
    '4(a)(iii)': '{{employment_start_year}}',
    
    # Employment end date
    '4(b)(i)': '{{employment_end_day}}',
    '4(b)(ii)': '{{employment_end_month}}',
    '4(b)(iii)': '{{employment_end_year}}',
    
    # Place of employment
    '5(a)': '{{workplace_location}}',
    
    # Work location details
    '5(b)(i)': '{{work_region}}',
    '5(b)(ii)': '{{work_district}}',
    '5(b)(iii)': '{{work_ward}}',
    
    # Job title and duties
    '6(a)': '{{job_title}}',
    '6(b)': '{{job_duties}}',
    
    # Probation period
    '7(a)': '{{probation_months}}',
    
    # Working hours
    '8(a)': '{{work_hours_per_day}}',
    '8(b)': '{{work_days_per_week}}',
    '8(c)(i)': '{{work_start_time}}',
    '8(c)(ii)': '{{work_end_time}}',
    
    # Salary details
    '9(a)': '{{salary_amount}}',
    '9(b)(i)': '{{salary_period_day}}',
    '9(b)(ii)': '{{salary_period_week}}',
    '9(b)(iii)': '{{salary_period_month}}',
    '9(c)': '{{payment_date}}',
    
    # Payment method
    '9(d)(i)': '{{payment_method_cash}}',
    '9(d)(ii)': '{{payment_method_bank}}',
    '9(d)(iii)': '{{payment_method_mobile}}',
    '9(d)(iv)': '{{payment_method_other}}',
    
    # Bank details
    '9(e)(i)': '{{bank_name}}',
    '9(e)(ii)': '{{bank_account_name}}',
    '9(e)(iii)': '{{bank_account_number}}',
    '9(e)(iv)': '{{bank_branch}}',
    
    # Allowances and benefits
    '10(a)(i)': '{{allowance_1}}',
    '10(a)(ii)': '{{allowance_2}}',
    '10(a)(iii)': '{{allowance_3}}',
    '10(a)(iv)': '{{allowance_4}}',
    '10(b)': '{{other_benefits}}',
}

# Read the extracted template
input_file = '/Users/mac/development/python_projects/pola-backend/extracted_templates/i. Mkataba wa Ajira.html'
output_file = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/i._mkataba_wa_ajira_clean.html'

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace placeholders with Django template variables
for placeholder, variable in field_mapping.items():
    # Wrap placeholders in data-field spans for bold styling
    content = content.replace(placeholder, f'<span class="data-field">{variable}</span>')

# Update CSS to include data-field styling
css_addition = """
.data-field { 
    font-weight: bold;
    border-bottom: 1px solid #000;
    padding: 0 5px;
    display: inline-block;
    min-width: 100px;
}
"""

# Insert CSS before closing style tag
content = content.replace('</style>', css_addition + '</style>')

# Clean up: remove excessive underscores and dots (keep structure clean)
import re
# Remove patterns like "___" or "………" that are just placeholders
content = re.sub(r'_{3,}', ' ', content)
content = re.sub(r'…{2,}', ' ', content)

# Write the converted template
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'✓ Swahili template converted successfully!')
print(f'✓ Input: {input_file}')
print(f'✓ Output: {output_file}')
print(f'✓ Total fields mapped: {len(field_mapping)}')
print('\nField mapping summary:')
print('  - Contract dates: 3 fields')
print('  - Employer details: 5 fields')
print('  - Employee details: 7 fields')
print('  - Employment dates: 6 fields')
print('  - Location: 4 fields')
print('  - Job details: 2 fields')
print('  - Probation: 1 field')
print('  - Working hours: 4 fields')
print('  - Salary: 7 fields')
print('  - Bank details: 4 fields')
print('  - Benefits: 5 fields')
print(f'  = Total: 48 fields')
