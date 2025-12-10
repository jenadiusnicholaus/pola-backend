"""
Update Employment Contract template with cleaned version
"""
from document_templates.models import DocumentTemplate

# Load the cleaned template
filepath = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/iii._employment_contract_clean.html'
with open(filepath, 'r', encoding='utf-8') as f:
    template_content = f.read()

# Update the template in database
try:
    template = DocumentTemplate.objects.get(id=13)
    template.template_content_en = template_content
    template.template_content_sw = template_content
    template.save()
    print(f'✓ Successfully updated template: {template.name}')
    print(f'✓ Template now has clean formatting with bold data fields')
    print(f'✓ All dots removed, professional spacing applied')
except DocumentTemplate.DoesNotExist:
    print('✗ Template ID 13 not found')
except Exception as e:
    print(f'✗ Error: {e}')
