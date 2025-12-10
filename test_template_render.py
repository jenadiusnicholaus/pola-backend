"""
Test script to check template rendering with sample data
"""
from django.template import Context, Template

# Load the template
template_path = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/iii._employment_contract.html'
with open(template_path, 'r', encoding='utf-8') as f:
    template_content = f.read()

# Sample data
data = {
    "contract_date_day": "10",
    "contract_date_month": "December",
    "contract_date_year": "2025",
    "employer_name": "ABC Company Ltd",
    "employer_address_street": "123 Business Street",
    "employer_address_city": "Dar es Salaam",
    "employer_phone": "+255 123 456 789",
    "employer_email": "hr@abccompany.co.tz",
    "employee_name": "John Doe",
    "employee_address_street": "456 Residential Road",
    "employee_address_city": "Dar es Salaam",
    "employee_phone": "+255 987 654 321",
    "employee_id_type": "National ID",
    "employee_id_number": "19900101-12345-67890-12",
    "employee_email": "john.doe@email.com",
    "employment_start_day": "1",
    "employment_start_month": "January",
    "employment_start_year": "2026",
    "employment_end_day": "31",
    "employment_end_month": "December",
    "employment_end_year": "2026",
    "workplace_location": "ABC Company Headquarters, Dar es Salaam",
    "work_region": "Dar es Salaam",
    "work_district": "Kinondoni",
    "work_ward": "Mikocheni",
    "job_title": "Senior Software Developer",
    "job_duties": "Develop software applications, Lead development team, Review code, Implement best practices",
    "probation_months": "3",
    "work_hours_per_day": "8",
    "work_days_per_week": "5",
    "work_start_time": "08:00",
    "work_end_time": "17:00",
    "salary_amount": "2500000",
    "salary_period_day": "",
    "salary_period_week": "",
    "salary_period_month": "Month",
    "payment_date": "25th",
    "payment_method_cash": "",
    "payment_method_bank": "Bank Transfer",
    "payment_method_mobile": "",
    "payment_method_other": "",
    "bank_name": "CRDB Bank",
    "bank_account_name": "John Doe",
    "bank_account_number": "0150123456789",
    "bank_branch": "Mikocheni Branch",
    "allowance_1": "Transport Allowance: TZS 200,000",
    "allowance_2": "Housing Allowance: TZS 500,000",
    "allowance_3": "Medical Insurance",
    "allowance_4": "Lunch Allowance: TZS 150,000",
    "other_benefits": "Annual bonus based on performance, Professional development training"
}

# Render
template = Template(template_content)
context = Context(data)
rendered = template.render(context)

# Check for unreplaced variables
import re
unreplaced = re.findall(r'\{\{([^}]+)\}\}', rendered)
if unreplaced:
    print(f"⚠️ Found {len(unreplaced)} unreplaced variables:")
    for var in set(unreplaced):
        print(f"  - {var}")
else:
    print("✓ All variables replaced successfully!")

# Save rendered HTML for inspection
output_path = '/Users/mac/development/python_projects/pola-backend/test_rendered.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(rendered)

print(f"\n✓ Rendered HTML saved to: {output_path}")
