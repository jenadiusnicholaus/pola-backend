"""
Script to convert extracted HTML templates with numbered placeholders
to Django-style templates with {{variable}} syntax
"""
import os
import re

def convert_placeholders_to_variables(html_content, template_name):
    """
    Convert numbered placeholders like 1(a), 2(b)(i) to {{variable_name}}
    based on context and position in the document
    """
    
    # Define field mappings based on template type
    field_mappings = {
        'Employment Contract': {
            '1(a)': '{{contract_date_day}}',
            '1(b)': '{{contract_date_month}}',
            '1(c)': '{{contract_date_year}}',
            '2(a)': '{{employer_name}}',
            '2(b)(i)': '{{employer_address_street}}',
            '2(b)(ii)': '{{employer_address_city}}',
            '2(c)': '{{employer_phone}}',
            '2(d)': '{{employer_email}}',
            '3(a)': '{{employee_name}}',
            '3(b)(i)': '{{employee_address_street}}',
            '3(b)(ii)': '{{employee_address_city}}',
            '3(c)': '{{employee_phone}}',
            '3(d)': '{{employee_id_type}}',
            '3(e)': '{{employee_id_number}}',
            '3(f)': '{{employee_email}}',
            '4(a)(i)': '{{employment_start_day}}',
            '4(a)(ii)': '{{employment_start_month}}',
            '4(a)(iii)': '{{employment_start_year}}',
            '4(b)(i)': '{{employment_end_day}}',
            '4(b)(ii)': '{{employment_end_month}}',
            '4(b)(iii)': '{{employment_end_year}}',
            '5(a)': '{{workplace_location}}',
            '5(b)(i)': '{{work_region}}',
            '5(b)(ii)': '{{work_district}}',
            '5(b)(iii)': '{{work_ward}}',
            '6(a)': '{{job_title}}',
            '6 (b)(i–x)': '{{job_duties}}',
            '7(a)': '{{probation_months}}',
            '8(a)': '{{work_hours_per_day}}',
            '8(b)': '{{work_days_per_week}}',
            '8(c)(i)': '{{work_start_time}}',
            '8(c)(ii)': '{{work_end_time}}',
            '9(a)': '{{salary_amount}}',
            '9(b)(i)': '{{salary_period_day}}',
            '9(b)(ii)': '{{salary_period_week}}',
            '9(b)(iii)': '{{salary_period_month}}',
            '9(c)': '{{payment_date}}',
            '9(d)(i)': '{{payment_method_cash}}',
            '9(d)(ii)': '{{payment_method_bank}}',
            '9(d)(iii)': '{{payment_method_mobile}}',
            '9(d)(iv)': '{{payment_method_other}}',
            '9(e)(i)': '{{bank_name}}',
            '9(e)(ii)': '{{bank_account_name}}',
            '9(e)(iii)': '{{bank_account_number}}',
            '9(e)(iv)': '{{bank_branch}}',
            '10(a)(i)': '{{allowance_1}}',
            '10(a)(ii)': '{{allowance_2}}',
            '10(a)(iii)': '{{allowance_3}}',
            '10(a)(iv)': '{{allowance_4}}',
            '10(b)': '{{other_benefits}}',
        },
        'Resignation': {
            '1(a)': '{{date_day}}',
            '1(b)': '{{date_month}}',
            '1(c)': '{{date_year}}',
            '2(a)': '{{employer_name}}',
            '2(b)': '{{employer_address}}',
            '3(a)': '{{employee_name}}',
            '3(b)': '{{employee_position}}',
            '4(a)': '{{resignation_date_day}}',
            '4(b)': '{{resignation_date_month}}',
            '4(c)': '{{resignation_date_year}}',
            '5(a)': '{{notice_period_days}}',
            '6(a)': '{{reason}}',
        },
        'Notice': {
            '1(a)': '{{notice_date_day}}',
            '1(b)': '{{notice_date_month}}',
            '1(c)': '{{notice_date_year}}',
            '2(a)': '{{recipient_name}}',
            '2(b)': '{{recipient_address}}',
            '3(a)': '{{sender_name}}',
            '3(b)': '{{sender_position}}',
            '4(a)': '{{subject}}',
            '5(a)': '{{notice_content}}',
            '6(a)': '{{effective_date}}',
        }
    }
    
    # Determine template type
    template_type = None
    if 'Employment Contract' in template_name:
        template_type = 'Employment Contract'
    elif 'Resignation' in template_name or 'Barua ya kujiuzulu' in template_name:
        template_type = 'Resignation'
    elif 'Notice' in template_name:
        template_type = 'Notice'
    
    if not template_type or template_type not in field_mappings:
        return html_content
    
    # Replace placeholders
    result = html_content
    for placeholder, variable in field_mappings[template_type].items():
        # Escape special regex characters in placeholder
        escaped_placeholder = re.escape(placeholder)
        # Replace the placeholder
        result = re.sub(escaped_placeholder, variable, result)
    
    return result

def process_templates():
    """Process all extracted HTML templates"""
    extracted_dir = '/Users/mac/development/python_projects/pola-backend/extracted_templates'
    output_dir = '/Users/mac/development/python_projects/pola-backend/document_templates/templates'
    
    os.makedirs(output_dir, exist_ok=True)
    
    templates_to_process = [
        'iii. Employment Contract.html',
        'iii. Resignation letter.html',
        'i. Barua ya kujiuzulu au Kuacha kazi.html',
        'iii. Notice (English).html',
        'iv. Questionnaire (English).html',
        'ii. Questionnaire (Kiswahili).html',
    ]
    
    for filename in templates_to_process:
        filepath = os.path.join(extracted_dir, filename)
        if not os.path.exists(filepath):
            print(f'⚠️  Skipping {filename} - file not found')
            continue
        
        print(f'\nProcessing: {filename}')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert placeholders
        converted_content = convert_placeholders_to_variables(content, filename)
        
        # Save to templates directory
        output_filename = filename.replace(' ', '_').lower()
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        print(f'  ✓ Saved to: {output_path}')
    
    print(f'\n✓ All templates processed and saved to: {output_dir}')

if __name__ == '__main__':
    process_templates()
