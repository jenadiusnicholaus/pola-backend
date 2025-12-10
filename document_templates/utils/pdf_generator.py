"""
PDF Generation Utility for Document Templates

Converts HTML templates to PDF with user data
Supports Swahili characters and custom styling
"""
from django.template import Context, Template
from django.conf import settings
import os
from datetime import datetime


class PDFGenerator:
    """
    Generate PDFs from HTML templates with user data
    """
    
    def __init__(self):
        self.base_css = """
        <style>
            @page {
                size: A4;
                margin: 2.5cm 2cm;
            }
            body {
                font-family: 'Times New Roman', 'DejaVu Serif', serif;
                font-size: 12pt;
                line-height: 1.8;
                color: #000;
                text-align: justify;
            }
            
            /* Header Styles */
            .document-header {
                text-align: center;
                margin-bottom: 40px;
                border-bottom: 3px double #000;
                padding-bottom: 20px;
            }
            .document-title {
                font-size: 20pt;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin: 20px 0;
            }
            .document-subtitle {
                font-size: 14pt;
                font-weight: bold;
                margin: 10px 0;
            }
            .document-ref {
                font-size: 11pt;
                margin: 5px 0;
            }
            
            /* Letter Header (for resignation, notice) */
            .letter-header {
                margin-bottom: 30px;
            }
            .sender-info {
                text-align: right;
                margin-bottom: 20px;
                line-height: 1.5;
            }
            .recipient-info {
                margin-bottom: 30px;
                line-height: 1.5;
            }
            
            /* Section Headings */
            h1 {
                font-size: 18pt;
                font-weight: bold;
                text-transform: uppercase;
                margin: 30px 0 20px 0;
                text-align: center;
                border-bottom: 2px solid #000;
                padding-bottom: 10px;
            }
            h2 {
                font-size: 14pt;
                font-weight: bold;
                text-transform: uppercase;
                margin: 25px 0 15px 0;
                background-color: #f0f0f0;
                padding: 8px 12px;
                border-left: 4px solid #000;
            }
            h3 {
                font-size: 12pt;
                font-weight: bold;
                margin: 20px 0 10px 0;
                text-decoration: underline;
            }
            
            /* Contract/Form Layout */
            .section {
                margin-bottom: 25px;
                page-break-inside: avoid;
            }
            .field-row {
                display: table;
                width: 100%;
                margin-bottom: 12px;
                page-break-inside: avoid;
            }
            .field-label {
                display: table-cell;
                font-weight: bold;
                width: 35%;
                vertical-align: top;
                padding-right: 10px;
            }
            .field-value {
                display: table-cell;
                width: 65%;
                border-bottom: 1px solid #000;
                padding: 4px 8px;
                vertical-align: top;
            }
            
            /* Box Layout for Important Info */
            .info-box {
                border: 2px solid #000;
                padding: 15px;
                margin: 20px 0;
                background-color: #f9f9f9;
            }
            .info-box-title {
                font-weight: bold;
                text-decoration: underline;
                margin-bottom: 10px;
            }
            
            /* Paragraphs */
            p {
                margin: 12px 0;
                text-indent: 0;
            }
            p.indented {
                text-indent: 30px;
            }
            .salutation {
                margin: 20px 0 10px 0;
            }
            .closing {
                margin: 30px 0 10px 0;
            }
            
            /* Tables */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 10px;
                border: 1px solid #000;
                text-align: left;
            }
            th {
                background-color: #e0e0e0;
                font-weight: bold;
                text-transform: uppercase;
            }
            
            /* Signature Section */
            .signature-section {
                margin-top: 60px;
                page-break-inside: avoid;
            }
            .signature-table {
                width: 100%;
                margin-top: 40px;
            }
            .signature-table td {
                border: none;
                vertical-align: bottom;
                text-align: center;
                width: 50%;
                padding: 0 20px;
            }
            .signature-line {
                border-top: 2px solid #000;
                margin-top: 60px;
                margin-bottom: 8px;
            }
            .signature-label {
                font-weight: bold;
                margin-top: 5px;
            }
            .signature-date {
                margin-top: 5px;
            }
            
            /* Terms and Conditions */
            .terms-list {
                margin: 15px 0;
                padding-left: 20px;
            }
            .terms-list li {
                margin: 8px 0;
            }
            
            /* Notice/Questionnaire specific */
            .question-block {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ccc;
                background-color: #fafafa;
            }
            .question {
                font-weight: bold;
                margin-bottom: 10px;
            }
            .answer {
                margin-left: 20px;
                padding: 10px;
                background-color: #fff;
                border-left: 3px solid #333;
            }
            
            /* Footer */
            .footer {
                margin-top: 60px;
                padding-top: 15px;
                border-top: 2px solid #000;
                font-size: 9pt;
                color: #666;
                text-align: center;
                font-style: italic;
            }
            
            /* Utilities */
            .text-center { text-align: center; }
            .text-right { text-align: right; }
            .text-left { text-align: left; }
            .bold { font-weight: bold; }
            .underline { text-decoration: underline; }
            .uppercase { text-transform: uppercase; }
            .page-break { page-break-after: always; }
        </style>
        """
    
    def render_template(self, template_content, data):
        """
        Render Django template with user data
        
        Args:
            template_content (str): HTML template with {{placeholders}}
            data (dict): User data to fill in template
        
        Returns:
            str: Rendered HTML
        """
        # Add current date and time to context
        context_data = data.copy()
        context_data['generated_date'] = datetime.now().strftime('%d/%m/%Y')
        context_data['generated_time'] = datetime.now().strftime('%H:%M')
        context_data['generated_datetime'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Create Django template and render
        template = Template(template_content)
        context = Context(context_data)
        rendered_html = template.render(context)
        
        return rendered_html
    
    def add_css(self, html_content):
        """
        Add base CSS styling to HTML
        
        Args:
            html_content (str): HTML content
        
        Returns:
            str: HTML with CSS
        """
        if '<head>' in html_content:
            return html_content.replace('<head>', f'<head>{self.base_css}')
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                {self.base_css}
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
    
    def html_to_pdf(self, html_content, output_path):
        """
        Convert HTML to PDF using xhtml2pdf (pure Python, no system dependencies)
        
        Args:
            html_content (str): HTML content
            output_path (str): Path to save PDF file
        
        Returns:
            str: Path to generated PDF
        """
        # Add custom CSS
        html_with_css = self.add_css(html_content)
        
        try:
            from xhtml2pdf import pisa
            
            # Create PDF from HTML
            with open(output_path, 'wb') as pdf_file:
                # Convert HTML to PDF
                pisa_status = pisa.CreatePDF(
                    html_with_css.encode('utf-8'),
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            # Check if PDF was created successfully
            if pisa_status.err:
                raise Exception(f"PDF generation had {pisa_status.err} error(s)")
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                raise Exception("PDF file was not created or is empty")
            
        except ImportError:
            # Fallback: Save as HTML if xhtml2pdf not available
            print("⚠️ xhtml2pdf not installed. Install with: pip install xhtml2pdf")
            print("Falling back to HTML output...")
            
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                warning_html = f"""
                <div style="background: #ffeb3b; padding: 20px; margin: 20px; border: 2px solid #f57c00;">
                    <h2 style="color: #d84315;">⚠️ PDF Generation Unavailable</h2>
                    <p><strong>Note:</strong> This document is displayed as HTML because xhtml2pdf is not installed.</p>
                    <p><strong>Solution:</strong> Run: pip install xhtml2pdf</p>
                </div>
                """
                f.write(warning_html + html_with_css)
            
            return html_path
            
        except Exception as e:
            # Fallback for any other errors
            print(f"PDF generation failed: {str(e)}")
            print("Falling back to HTML output...")
            
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                warning_html = f"""
                <div style="background: #ffeb3b; padding: 20px; margin: 20px; border: 2px solid #f57c00;">
                    <h2 style="color: #d84315;">⚠️ PDF Generation Error</h2>
                    <p><strong>Error:</strong> {str(e)}</p>
                    <p>Document saved as HTML for review.</p>
                </div>
                """
                f.write(warning_html + html_with_css)
            
            return html_path
    
    def generate_document(self, template_content, user_data, output_path):
        """
        Complete document generation pipeline
        
        Args:
            template_content (str): HTML template
            user_data (dict): User's filled data
            output_path (str): Path to save PDF
        
        Returns:
            str: Path to generated PDF
        """
        # Step 1: Render template with data
        rendered_html = self.render_template(template_content, user_data)
        
        # Step 2: Convert to PDF
        pdf_path = self.html_to_pdf(rendered_html, output_path)
        
        return pdf_path


def validate_field_data(field, value):
    """
    Validate field data against validation rules
    
    Args:
        field (TemplateField): Field instance
        value (str): User's input
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if required
    if field.is_required and not value:
        return False, f"{field.label_en} is required"
    
    # Get validation rules
    rules = field.get_validation_rules()
    
    # Min length
    if 'min_length' in rules and len(value) < rules['min_length']:
        return False, f"{field.label_en} must be at least {rules['min_length']} characters"
    
    # Max length
    if 'max_length' in rules and len(value) > rules['max_length']:
        return False, f"{field.label_en} must be at most {rules['max_length']} characters"
    
    # Pattern matching
    if 'pattern' in rules:
        import re
        if not re.match(rules['pattern'], value):
            error_msg = rules.get('pattern_error', f"{field.label_en} format is invalid")
            return False, error_msg
    
    # Email validation
    if field.field_type == 'email':
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return False, f"{field.label_en} must be a valid email address"
    
    # Phone validation (basic)
    if field.field_type == 'phone':
        import re
        # Remove spaces and dashes
        clean_phone = value.replace(' ', '').replace('-', '')
        if not re.match(r'^\+?[0-9]{9,15}$', clean_phone):
            return False, f"{field.label_en} must be a valid phone number"
    
    # Number validation
    if field.field_type == 'number':
        try:
            float(value)
        except ValueError:
            return False, f"{field.label_en} must be a valid number"
    
    return True, None
