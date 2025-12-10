#!/usr/bin/env python
"""Test WeasyPrint PDF generation"""

from weasyprint import HTML
import os

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Document</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2cm; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Test Document</h1>
    <p>This is a test PDF generation.</p>
    <p>If you can see this, WeasyPrint is working correctly!</p>
</body>
</html>"""

try:
    output_path = '/tmp/test_weasyprint.pdf'
    HTML(string=html_content).write_pdf(output_path)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f'✅ PDF generation successful!')
        print(f'✅ File: {output_path}')
        print(f'✅ Size: {size:,} bytes')
    else:
        print('❌ PDF file was not created')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
