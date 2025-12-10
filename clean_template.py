"""
Script to clean up the employment contract template:
1. Remove all dots (...) before and after variables
2. Make all variable data bold with underline
3. Keep professional spacing
"""
import re

template_path = '/Users/mac/development/python_projects/pola-backend/document_templates/templates/iii._employment_contract.html'

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Function to clean up around variables
def clean_variable_formatting(match):
    """Clean dots around {{variable}} and add bold styling"""
    before = match.group(1)
    var_name = match.group(2)
    after = match.group(3)
    
    # Remove dots and excessive spaces before variable
    before_clean = re.sub(r'[\.…]+\s*$', ' ', before)
    before_clean = before_clean.rstrip()
    if before_clean and not before_clean.endswith(' '):
        before_clean += ' '
    
    # Remove dots and excessive spaces after variable
    after_clean = re.sub(r'^\s*[\.…]+', ' ', after)
    after_clean = after_clean.lstrip()
    if after_clean and not after_clean.startswith(' ') and not after_clean.startswith(',') and not after_clean.startswith('.'):
        after_clean = ' ' + after_clean
    
    # Return with bold styling
    return f'{before_clean}<span class="data-field">{{{{var_name}}}}</span>{after_clean}'

# Pattern to match text before {{variable}}, the variable, and text after
# This will match across span tags
pattern = r'([^{]*)\{\{([^}]+)\}\}([^{]*?)(?=\{\{|</span>|</p>|$)'

# First, let's simplify by removing the span wrapping around variables temporarily
content = re.sub(r'<span[^>]*>\s*(\{\{[^}]+\}\})\s*</span>', r'\1', content)

# Now clean up dots around all variables
while True:
    new_content = re.sub(
        r'([^{]{0,100})\{\{([^}]+)\}\}([^{]{0,100})',
        lambda m: clean_variable_formatting(m),
        content,
        count=1
    )
    if new_content == content:
        break
    content = new_content

# Clean up remaining standalone dots patterns
content = re.sub(r'<span>\s*[\.…]+\s*</span>', '', content)
content = re.sub(r'[\.…]{3,}', '', content)

# Save the cleaned template
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Template cleaned successfully!")
print("  - Removed all dots around variables")
print("  - Applied bold styling to all data fields")
print("  - Maintained professional spacing")
