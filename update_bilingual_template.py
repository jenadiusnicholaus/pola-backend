#!/usr/bin/env python
"""Update database with Swahili Employment Contract template"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/Users/mac/development/python_projects/pola-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pola_settings.settings')
django.setup()

from document_templates.models import DocumentTemplate

# Read the Swahili template
filepath = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/i._mkataba_wa_ajira_clean.html'
with open(filepath, 'r', encoding='utf-8') as f:
    swahili_content = f.read()

# Read the English template for reference
english_filepath = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/iii._employment_contract_clean.html'
with open(english_filepath, 'r', encoding='utf-8') as f:
    english_content = f.read()

# Update the template (ID 13) with both English and Swahili versions
try:
    template = DocumentTemplate.objects.get(id=13)
    template.template_content_en = english_content
    template.template_content_sw = swahili_content
    template.save()
    
    print('✓ Successfully updated template: Employment Contract')
    print('✓ English version updated')
    print('✓ Swahili version updated (Mkataba wa Ajira)')
    print('✓ Template now supports both languages')
    print(f'✓ Template ID: {template.id}')
    print(f'✓ Template Name: {template.name}')
except DocumentTemplate.DoesNotExist:
    print('✗ Template with ID 13 not found')
    print('  Please create the template first')
except Exception as e:
    print(f'✗ Error updating template: {e}')
