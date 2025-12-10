"""
Django management command to seed document templates

Usage:
    python manage.py seed_templates
    python manage.py seed_templates --clear  # Clear existing templates first
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from document_templates.models import (
    DocumentTemplate,
    TemplateSection,
    TemplateField
)
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Seeds document templates with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before seeding',
        )
    
    def load_template_file(self, filename):
        """Load HTML template content from file"""
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        filepath = os.path.join(template_dir, filename)
        
        if not os.path.exists(filepath):
            self.stdout.write(self.style.WARNING(f'Template file not found: {filepath}'))
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing templates...')
            DocumentTemplate.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared'))

        self.stdout.write('Seeding document templates...\n')

        # 1. Employment Contract (Mkataba wa Ajira)
        self.create_employment_contract()
        
        # 2. Resignation Letter (Barua ya Kujiuzulu)
        self.create_resignation_letter()
        
        # 3. Notice (Ilani)
        self.create_notice()
        
        # 4. Questionnaire (Dodoso)
        self.create_questionnaire()
        
        # 5. Employment Form (Fomu ya Kujiungua/Kuacha Kazi)
        self.create_employment_form()

        self.stdout.write(self.style.SUCCESS('\n✓ All templates seeded successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Total templates: {DocumentTemplate.objects.count()}'))

    def create_employment_contract(self):
        """Create Employment Contract template"""
        self.stdout.write('Creating: Employment Contract (Mkataba wa Ajira)...')
        
        template = DocumentTemplate.objects.create(
            name='Employment Contract',
            name_sw='Mkataba wa Ajira',
            description='Standard employment contract between employer and employee',
            description_sw='Mkataba wa kawaida wa ajira kati ya mwajiri na mwajiriwa',
            category='employment',
            is_free=True,
            icon='📄',
            order=1,
            template_content_en='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Employment Contract</title>
</head>
<body>
    <h1>EMPLOYMENT CONTRACT</h1>
    
    <p><strong>Date:</strong> {{generated_date}}</p>
    
    <h2>EMPLOYER INFORMATION</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Company Name:</div>
            <div class="field-value">{{company_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Address:</div>
            <div class="field-value">{{company_address}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Phone:</div>
            <div class="field-value">{{company_phone}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Email:</div>
            <div class="field-value">{{company_email}}</div>
        </div>
    </div>
    
    <h2>EMPLOYEE INFORMATION</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Full Name:</div>
            <div class="field-value">{{employee_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">ID Number:</div>
            <div class="field-value">{{employee_id}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Address:</div>
            <div class="field-value">{{employee_address}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Phone:</div>
            <div class="field-value">{{employee_phone}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Email:</div>
            <div class="field-value">{{employee_email}}</div>
        </div>
    </div>
    
    <h2>EMPLOYMENT DETAILS</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Position:</div>
            <div class="field-value">{{position}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Department:</div>
            <div class="field-value">{{department}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Start Date:</div>
            <div class="field-value">{{start_date}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Salary:</div>
            <div class="field-value">{{salary}} TZS per month</div>
        </div>
        <div class="field-group">
            <div class="field-label">Working Hours:</div>
            <div class="field-value">{{working_hours}}</div>
        </div>
    </div>
    
    <h2>TERMS & CONDITIONS</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Probation Period:</div>
            <div class="field-value">{{probation_period}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Notice Period:</div>
            <div class="field-value">{{notice_period}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Annual Leave:</div>
            <div class="field-value">{{annual_leave}} days</div>
        </div>
    </div>
    
    <div class="signature-section">
        <h3>SIGNATURES</h3>
        <table>
            <tr>
                <td>
                    <div class="signature-line"></div>
                    <p>Employee Signature</p>
                    <p>Date: {{employee_sign_date}}</p>
                </td>
                <td>
                    <div class="signature-line"></div>
                    <p>Employer Signature</p>
                    <p>Date: {{employer_sign_date}}</p>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Generated by Pola Legal Platform on {{generated_datetime}}</p>
    </div>
</body>
</html>
            ''',
            template_content_sw='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mkataba wa Ajira</title>
</head>
<body>
    <h1>MKATABA WA AJIRA</h1>
    
    <p><strong>Tarehe:</strong> {{generated_date}}</p>
    
    <h2>TAARIFA ZA MWAJIRI</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Jina la Kampuni:</div>
            <div class="field-value">{{company_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Anwani:</div>
            <div class="field-value">{{company_address}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Simu:</div>
            <div class="field-value">{{company_phone}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Barua Pepe:</div>
            <div class="field-value">{{company_email}}</div>
        </div>
    </div>
    
    <h2>TAARIFA ZA MWAJIRIWA</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Jina Kamili:</div>
            <div class="field-value">{{employee_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Namba ya Kitambulisho:</div>
            <div class="field-value">{{employee_id}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Anwani:</div>
            <div class="field-value">{{employee_address}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Simu:</div>
            <div class="field-value">{{employee_phone}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Barua Pepe:</div>
            <div class="field-value">{{employee_email}}</div>
        </div>
    </div>
    
    <h2>MAELEZO YA AJIRA</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Nafasi:</div>
            <div class="field-value">{{position}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Idara:</div>
            <div class="field-value">{{department}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Tarehe ya Kuanza:</div>
            <div class="field-value">{{start_date}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Mshahara:</div>
            <div class="field-value">{{salary}} TZS kwa mwezi</div>
        </div>
        <div class="field-group">
            <div class="field-label">Masaa ya Kazi:</div>
            <div class="field-value">{{working_hours}}</div>
        </div>
    </div>
    
    <h2>MASHARTI NA HALI</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Kipindi cha Mtihani:</div>
            <div class="field-value">{{probation_period}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Kipindi cha Notisi:</div>
            <div class="field-value">{{notice_period}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Likizo ya Mwaka:</div>
            <div class="field-value">{{annual_leave}} siku</div>
        </div>
    </div>
    
    <div class="signature-section">
        <h3>SAINI</h3>
        <table>
            <tr>
                <td>
                    <div class="signature-line"></div>
                    <p>Saini ya Mwajiriwa</p>
                    <p>Tarehe: {{employee_sign_date}}</p>
                </td>
                <td>
                    <div class="signature-line"></div>
                    <p>Saini ya Mwajiri</p>
                    <p>Tarehe: {{employer_sign_date}}</p>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Imetengenezwa na Jukwaa la Kisheria la Pola tarehe {{generated_datetime}}</p>
    </div>
</body>
</html>
            '''
        )
        
        # Create sections
        employer_section = TemplateSection.objects.create(
            template=template,
            name='Employer Information',
            name_sw='Taarifa za Mwajiri',
            order=1
        )
        
        employee_section = TemplateSection.objects.create(
            template=template,
            name='Employee Information',
            name_sw='Taarifa za Mwajiriwa',
            order=2
        )
        
        employment_section = TemplateSection.objects.create(
            template=template,
            name='Employment Details',
            name_sw='Maelezo ya Ajira',
            order=3
        )
        
        terms_section = TemplateSection.objects.create(
            template=template,
            name='Terms & Conditions',
            name_sw='Masharti na Hali',
            order=4
        )
        
        signature_section = TemplateSection.objects.create(
            template=template,
            name='Signatures',
            name_sw='Saini',
            order=5
        )
        
        # Create fields
        fields_data = [
            # Employer Information
            ('company_name', 'Company Name', 'Jina la Kampuni', 'text', employer_section, 1, True, 'Enter company name', 'Weka jina la kampuni'),
            ('company_address', 'Company Address', 'Anwani ya Kampuni', 'textarea', employer_section, 2, True, 'Enter company address', 'Weka anwani ya kampuni'),
            ('company_phone', 'Company Phone', 'Simu ya Kampuni', 'phone', employer_section, 3, True, '+255 XXX XXX XXX', '+255 XXX XXX XXX'),
            ('company_email', 'Company Email', 'Barua Pepe ya Kampuni', 'email', employer_section, 4, True, 'company@example.com', 'kampuni@mfano.com'),
            
            # Employee Information
            ('employee_name', 'Employee Full Name', 'Jina Kamili la Mwajiriwa', 'text', employee_section, 1, True, 'Enter full name', 'Weka jina kamili'),
            ('employee_id', 'Employee ID Number', 'Namba ya Kitambulisho', 'text', employee_section, 2, True, 'ID number', 'Namba ya kitambulisho'),
            ('employee_address', 'Employee Address', 'Anwani ya Mwajiriwa', 'textarea', employee_section, 3, True, 'Enter address', 'Weka anwani'),
            ('employee_phone', 'Employee Phone', 'Simu ya Mwajiriwa', 'phone', employee_section, 4, True, '+255 XXX XXX XXX', '+255 XXX XXX XXX'),
            ('employee_email', 'Employee Email', 'Barua Pepe ya Mwajiriwa', 'email', employee_section, 5, True, 'employee@example.com', 'mwajiriwa@mfano.com'),
            
            # Employment Details
            ('position', 'Position/Job Title', 'Nafasi/Cheo', 'text', employment_section, 1, True, 'e.g., Software Engineer', 'mfano, Mhandisi Programu'),
            ('department', 'Department', 'Idara', 'text', employment_section, 2, True, 'e.g., IT Department', 'mfano, Idara ya IT'),
            ('start_date', 'Start Date', 'Tarehe ya Kuanza', 'date', employment_section, 3, True, 'YYYY-MM-DD', 'MWAKA-MWEZI-SIKU'),
            ('salary', 'Monthly Salary (TZS)', 'Mshahara wa Mwezi (TZS)', 'number', employment_section, 4, True, 'e.g., 1500000', 'mfano, 1500000'),
            ('working_hours', 'Working Hours', 'Masaa ya Kazi', 'text', employment_section, 5, True, 'e.g., 40 hours per week', 'mfano, Masaa 40 kwa wiki'),
            
            # Terms & Conditions
            ('probation_period', 'Probation Period', 'Kipindi cha Mtihani', 'text', terms_section, 1, True, 'e.g., 3 months', 'mfano, Miezi 3'),
            ('notice_period', 'Notice Period', 'Kipindi cha Notisi', 'text', terms_section, 2, True, 'e.g., 30 days', 'mfano, Siku 30'),
            ('annual_leave', 'Annual Leave Days', 'Siku za Likizo ya Mwaka', 'number', terms_section, 3, True, 'e.g., 28', 'mfano, 28'),
            
            # Signatures
            ('employee_sign_date', 'Employee Signature Date', 'Tarehe ya Saini ya Mwajiriwa', 'date', signature_section, 1, True, 'YYYY-MM-DD', 'MWAKA-MWEZI-SIKU'),
            ('employer_sign_date', 'Employer Signature Date', 'Tarehe ya Saini ya Mwajiri', 'date', signature_section, 2, True, 'YYYY-MM-DD', 'MWAKA-MWEZI-SIKU'),
        ]
        
        for field_data in fields_data:
            field_name, label_en, label_sw, field_type, section, order, required, placeholder_en, placeholder_sw = field_data
            TemplateField.objects.create(
                template=template,
                section=section,
                field_name=field_name,
                label_en=label_en,
                label_sw=label_sw,
                field_type=field_type,
                order=order,
                is_required=required,
                placeholder_en=placeholder_en,
                placeholder_sw=placeholder_sw
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Employment Contract created'))

    def create_resignation_letter(self):
        """Create Resignation Letter template"""
        self.stdout.write('Creating: Resignation Letter (Barua ya Kujiuzulu)...')
        
        template = DocumentTemplate.objects.create(
            name='Resignation Letter',
            name_sw='Barua ya Kujiuzulu',
            description='Professional resignation letter template',
            description_sw='Kiolezo cha barua ya kujiuzulu kwa kitaalamu',
            category='resignation',
            is_free=True,
            icon='✉️',
            order=2,
            template_content_en='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Resignation Letter</title>
</head>
<body>
    <div style="text-align: right;">
        <p>{{employee_name}}<br>
        {{employee_address}}<br>
        {{employee_phone}}<br>
        {{employee_email}}</p>
        <p>{{letter_date}}</p>
    </div>
    
    <div>
        <p>{{manager_name}}<br>
        {{manager_title}}<br>
        {{company_name}}<br>
        {{company_address}}</p>
    </div>
    
    <h2>RESIGNATION LETTER</h2>
    
    <p>Dear {{manager_name}},</p>
    
    <p>I am writing to formally notify you of my resignation from my position as <strong>{{position}}</strong> 
    at <strong>{{company_name}}</strong>, effective <strong>{{last_working_day}}</strong>.</p>
    
    <p><strong>Reason for Resignation:</strong><br>
    {{resignation_reason}}</p>
    
    <p>I am providing <strong>{{notice_period}}</strong> notice as per my employment contract.</p>
    
    <p>I would like to express my gratitude for the opportunities I have been given during my time with the company. 
    I have learned a great deal and enjoyed working with the team.</p>
    
    <p>I am committed to ensuring a smooth transition and will do everything possible to hand over my responsibilities 
    before my departure.</p>
    
    <p>Thank you for your understanding.</p>
    
    <div class="signature-section">
        <p>Sincerely,</p>
        <div class="signature-line"></div>
        <p>{{employee_name}}</p>
        <p>Date: {{letter_date}}</p>
    </div>
    
    <div class="footer">
        <p>Generated by Pola Legal Platform on {{generated_datetime}}</p>
    </div>
</body>
</html>
            ''',
            template_content_sw='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Barua ya Kujiuzulu</title>
</head>
<body>
    <div style="text-align: right;">
        <p>{{employee_name}}<br>
        {{employee_address}}<br>
        {{employee_phone}}<br>
        {{employee_email}}</p>
        <p>{{letter_date}}</p>
    </div>
    
    <div>
        <p>{{manager_name}}<br>
        {{manager_title}}<br>
        {{company_name}}<br>
        {{company_address}}</p>
    </div>
    
    <h2>BARUA YA KUJIUZULU</h2>
    
    <p>Mpendwa {{manager_name}},</p>
    
    <p>Naandika kukujulisha rasmi kuhusu uamuzi wangu wa kujiuzulu kutoka nafasi yangu ya <strong>{{position}}</strong> 
    katika <strong>{{company_name}}</strong>, kuanzia <strong>{{last_working_day}}</strong>.</p>
    
    <p><strong>Sababu ya Kujiuzulu:</strong><br>
    {{resignation_reason}}</p>
    
    <p>Ninatoa notisi ya <strong>{{notice_period}}</strong> kama ilivyoainishwa katika mkataba wangu wa ajira.</p>
    
    <p>Ningependa kutoa shukrani zangu kwa fursa nilizopewa wakati wangu na kampuni. 
    Nimejifunza mengi na nimefurahia kufanya kazi na timu.</p>
    
    <p>Nimejitolea kuhakikisha mpito unaofaa na nitafanya kila linalowezekana kupitisha majukumu yangu 
    kabla ya kuondoka kwangu.</p>
    
    <p>Asante kwa uelewa wako.</p>
    
    <div class="signature-section">
        <p>Wako mwaminifu,</p>
        <div class="signature-line"></div>
        <p>{{employee_name}}</p>
        <p>Tarehe: {{letter_date}}</p>
    </div>
    
    <div class="footer">
        <p>Imetengenezwa na Jukwaa la Kisheria la Pola tarehe {{generated_datetime}}</p>
    </div>
</body>
</html>
            '''
        )
        
        # Create fields (no sections for simpler letter format)
        fields = [
            ('employee_name', 'Your Full Name', 'Jina Lako Kamili', 'text', 1, True),
            ('employee_address', 'Your Address', 'Anwani Yako', 'textarea', 2, True),
            ('employee_phone', 'Your Phone', 'Simu Yako', 'phone', 3, True),
            ('employee_email', 'Your Email', 'Barua Pepe Yako', 'email', 4, True),
            ('letter_date', 'Letter Date', 'Tarehe ya Barua', 'date', 5, True),
            ('manager_name', 'Manager Name', 'Jina la Msimamizi', 'text', 6, True),
            ('manager_title', 'Manager Title', 'Cheo cha Msimamizi', 'text', 7, True),
            ('company_name', 'Company Name', 'Jina la Kampuni', 'text', 8, True),
            ('company_address', 'Company Address', 'Anwani ya Kampuni', 'textarea', 9, True),
            ('position', 'Your Position', 'Nafasi Yako', 'text', 10, True),
            ('last_working_day', 'Last Working Day', 'Siku ya Mwisho ya Kufanya Kazi', 'date', 11, True),
            ('resignation_reason', 'Reason for Resignation', 'Sababu ya Kujiuzulu', 'textarea', 12, True),
            ('notice_period', 'Notice Period', 'Kipindi cha Notisi', 'text', 13, True),
        ]
        
        for field_name, label_en, label_sw, field_type, order, required in fields:
            TemplateField.objects.create(
                template=template,
                field_name=field_name,
                label_en=label_en,
                label_sw=label_sw,
                field_type=field_type,
                order=order,
                is_required=required
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Resignation Letter created'))

    def create_notice(self):
        """Create Notice template"""
        self.stdout.write('Creating: Notice (Ilani)...')
        
        template = DocumentTemplate.objects.create(
            name='Official Notice',
            name_sw='Ilani Rasmi',
            description='General purpose official notice template',
            description_sw='Kiolezo cha ilani rasmi kwa matumizi ya jumla',
            category='legal_notice',
            is_free=True,
            icon='📢',
            order=3,
            template_content_en='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Official Notice</title>
</head>
<body>
    <div style="text-align: center;">
        <h1>OFFICIAL NOTICE</h1>
        <p><strong>{{notice_title}}</strong></p>
        <p>Date: {{notice_date}}</p>
        <p>Reference No: {{reference_number}}</p>
    </div>
    
    <h2>TO WHOM IT MAY CONCERN</h2>
    
    <div class="section">
        <p><strong>From:</strong> {{issuer_name}}<br>
        <strong>Organization:</strong> {{organization_name}}<br>
        <strong>Address:</strong> {{organization_address}}</p>
    </div>
    
    <h2>NOTICE DETAILS</h2>
    
    <p><strong>Subject:</strong> {{subject}}</p>
    
    <p><strong>Notice Content:</strong></p>
    <div class="field-value">{{notice_content}}</div>
    
    <p><strong>Effective Date:</strong> {{effective_date}}</p>
    
    <p><strong>Action Required:</strong></p>
    <div class="field-value">{{action_required}}</div>
    
    <p><strong>Deadline:</strong> {{deadline}}</p>
    
    <p><strong>Contact Information:</strong><br>
    Phone: {{contact_phone}}<br>
    Email: {{contact_email}}</p>
    
    <div class="signature-section">
        <div class="signature-line"></div>
        <p>{{issuer_name}}<br>
        {{issuer_title}}<br>
        {{organization_name}}<br>
        Date: {{notice_date}}</p>
    </div>
    
    <div class="footer">
        <p>Generated by Pola Legal Platform on {{generated_datetime}}</p>
    </div>
</body>
</html>
            ''',
            template_content_sw='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ilani Rasmi</title>
</head>
<body>
    <div style="text-align: center;">
        <h1>ILANI RASMI</h1>
        <p><strong>{{notice_title}}</strong></p>
        <p>Tarehe: {{notice_date}}</p>
        <p>Namba ya Kumbukumbu: {{reference_number}}</p>
    </div>
    
    <h2>KWA WOTE WANAOHUSIKA</h2>
    
    <div class="section">
        <p><strong>Kutoka:</strong> {{issuer_name}}<br>
        <strong>Shirika:</strong> {{organization_name}}<br>
        <strong>Anwani:</strong> {{organization_address}}</p>
    </div>
    
    <h2>MAELEZO YA ILANI</h2>
    
    <p><strong>Mada:</strong> {{subject}}</p>
    
    <p><strong>Maudhui ya Ilani:</strong></p>
    <div class="field-value">{{notice_content}}</div>
    
    <p><strong>Tarehe ya Kuanza Kutumika:</strong> {{effective_date}}</p>
    
    <p><strong>Hatua Inayohitajika:</strong></p>
    <div class="field-value">{{action_required}}</div>
    
    <p><strong>Muda wa Mwisho:</strong> {{deadline}}</p>
    
    <p><strong>Mawasiliano:</strong><br>
    Simu: {{contact_phone}}<br>
    Barua Pepe: {{contact_email}}</p>
    
    <div class="signature-section">
        <div class="signature-line"></div>
        <p>{{issuer_name}}<br>
        {{issuer_title}}<br>
        {{organization_name}}<br>
        Tarehe: {{notice_date}}</p>
    </div>
    
    <div class="footer">
        <p>Imetengenezwa na Jukwaa la Kisheria la Pola tarehe {{generated_datetime}}</p>
    </div>
</body>
</html>
            '''
        )
        
        fields = [
            ('notice_title', 'Notice Title', 'Kichwa cha Ilani', 'text', 1, True),
            ('notice_date', 'Notice Date', 'Tarehe ya Ilani', 'date', 2, True),
            ('reference_number', 'Reference Number', 'Namba ya Kumbukumbu', 'text', 3, True),
            ('issuer_name', 'Issuer Name', 'Jina la Mtoa', 'text', 4, True),
            ('issuer_title', 'Issuer Title', 'Cheo cha Mtoa', 'text', 5, True),
            ('organization_name', 'Organization Name', 'Jina la Shirika', 'text', 6, True),
            ('organization_address', 'Organization Address', 'Anwani ya Shirika', 'textarea', 7, True),
            ('subject', 'Subject', 'Mada', 'text', 8, True),
            ('notice_content', 'Notice Content', 'Maudhui ya Ilani', 'textarea', 9, True),
            ('effective_date', 'Effective Date', 'Tarehe ya Kuanza Kutumika', 'date', 10, True),
            ('action_required', 'Action Required', 'Hatua Inayohitajika', 'textarea', 11, True),
            ('deadline', 'Deadline', 'Muda wa Mwisho', 'date', 12, True),
            ('contact_phone', 'Contact Phone', 'Simu ya Mawasiliano', 'phone', 13, True),
            ('contact_email', 'Contact Email', 'Barua Pepe ya Mawasiliano', 'email', 14, True),
        ]
        
        for field_name, label_en, label_sw, field_type, order, required in fields:
            TemplateField.objects.create(
                template=template,
                field_name=field_name,
                label_en=label_en,
                label_sw=label_sw,
                field_type=field_type,
                order=order,
                is_required=required
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Notice created'))

    def create_questionnaire(self):
        """Create Questionnaire template"""
        self.stdout.write('Creating: Questionnaire (Dodoso)...')
        
        template = DocumentTemplate.objects.create(
            name='Questionnaire',
            name_sw='Dodoso',
            description='General purpose questionnaire/survey template',
            description_sw='Kiolezo cha dodoso/utafiti kwa matumizi ya jumla',
            category='questionnaire',
            is_free=True,
            icon='📝',
            order=4,
            template_content_en='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Questionnaire</title>
</head>
<body>
    <h1>QUESTIONNAIRE</h1>
    
    <p><strong>Title:</strong> {{questionnaire_title}}</p>
    <p><strong>Date:</strong> {{questionnaire_date}}</p>
    <p><strong>Conducted By:</strong> {{conductor_name}}</p>
    <p><strong>Organization:</strong> {{organization}}</p>
    
    <h2>RESPONDENT INFORMATION</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Full Name:</div>
            <div class="field-value">{{respondent_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Age:</div>
            <div class="field-value">{{respondent_age}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Gender:</div>
            <div class="field-value">{{respondent_gender}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Occupation:</div>
            <div class="field-value">{{respondent_occupation}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Contact:</div>
            <div class="field-value">{{respondent_contact}}</div>
        </div>
    </div>
    
    <h2>QUESTIONS</h2>
    
    <div class="section">
        <h3>Question 1:</h3>
        <p>{{question_1}}</p>
        <p><strong>Answer:</strong> {{answer_1}}</p>
    </div>
    
    <div class="section">
        <h3>Question 2:</h3>
        <p>{{question_2}}</p>
        <p><strong>Answer:</strong> {{answer_2}}</p>
    </div>
    
    <div class="section">
        <h3>Question 3:</h3>
        <p>{{question_3}}</p>
        <p><strong>Answer:</strong> {{answer_3}}</p>
    </div>
    
    <div class="section">
        <h3>Additional Comments:</h3>
        <div class="field-value">{{additional_comments}}</div>
    </div>
    
    <div class="signature-section">
        <p>Respondent Signature:</p>
        <div class="signature-line"></div>
        <p>Date: {{signature_date}}</p>
    </div>
    
    <div class="footer">
        <p>Generated by Pola Legal Platform on {{generated_datetime}}</p>
    </div>
</body>
</html>
            ''',
            template_content_sw='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dodoso</title>
</head>
<body>
    <h1>DODOSO</h1>
    
    <p><strong>Kichwa:</strong> {{questionnaire_title}}</p>
    <p><strong>Tarehe:</strong> {{questionnaire_date}}</p>
    <p><strong>Imefanywa na:</strong> {{conductor_name}}</p>
    <p><strong>Shirika:</strong> {{organization}}</p>
    
    <h2>TAARIFA ZA MHOJIWA</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Jina Kamili:</div>
            <div class="field-value">{{respondent_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Umri:</div>
            <div class="field-value">{{respondent_age}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Jinsia:</div>
            <div class="field-value">{{respondent_gender}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Kazi:</div>
            <div class="field-value">{{respondent_occupation}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Mawasiliano:</div>
            <div class="field-value">{{respondent_contact}}</div>
        </div>
    </div>
    
    <h2>MASWALI</h2>
    
    <div class="section">
        <h3>Swali la 1:</h3>
        <p>{{question_1}}</p>
        <p><strong>Jibu:</strong> {{answer_1}}</p>
    </div>
    
    <div class="section">
        <h3>Swali la 2:</h3>
        <p>{{question_2}}</p>
        <p><strong>Jibu:</strong> {{answer_2}}</p>
    </div>
    
    <div class="section">
        <h3>Swali la 3:</h3>
        <p>{{question_3}}</p>
        <p><strong>Jibu:</strong> {{answer_3}}</p>
    </div>
    
    <div class="section">
        <h3>Maoni Zaidi:</h3>
        <div class="field-value">{{additional_comments}}</div>
    </div>
    
    <div class="signature-section">
        <p>Saini ya Mhojiwa:</p>
        <div class="signature-line"></div>
        <p>Tarehe: {{signature_date}}</p>
    </div>
    
    <div class="footer">
        <p>Imetengenezwa na Jukwaa la Kisheria la Pola tarehe {{generated_datetime}}</p>
    </div>
</body>
</html>
            '''
        )
        
        fields = [
            ('questionnaire_title', 'Questionnaire Title', 'Kichwa cha Dodoso', 'text', 1, True),
            ('questionnaire_date', 'Date', 'Tarehe', 'date', 2, True),
            ('conductor_name', 'Conductor Name', 'Jina la Mfanyaji', 'text', 3, True),
            ('organization', 'Organization', 'Shirika', 'text', 4, True),
            ('respondent_name', 'Respondent Full Name', 'Jina Kamili la Mhojiwa', 'text', 5, True),
            ('respondent_age', 'Age', 'Umri', 'number', 6, True),
            ('respondent_gender', 'Gender', 'Jinsia', 'dropdown', 7, True),
            ('respondent_occupation', 'Occupation', 'Kazi', 'text', 8, True),
            ('respondent_contact', 'Contact', 'Mawasiliano', 'phone', 9, True),
            ('question_1', 'Question 1', 'Swali la 1', 'textarea', 10, True),
            ('answer_1', 'Answer 1', 'Jibu la 1', 'textarea', 11, True),
            ('question_2', 'Question 2', 'Swali la 2', 'textarea', 12, True),
            ('answer_2', 'Answer 2', 'Jibu la 2', 'textarea', 13, True),
            ('question_3', 'Question 3', 'Swali la 3', 'textarea', 14, True),
            ('answer_3', 'Answer 3', 'Jibu la 3', 'textarea', 15, True),
            ('additional_comments', 'Additional Comments', 'Maoni Zaidi', 'textarea', 16, False),
            ('signature_date', 'Signature Date', 'Tarehe ya Saini', 'date', 17, True),
        ]
        
        for field_name, label_en, label_sw, field_type, order, required in fields:
            field = TemplateField.objects.create(
                template=template,
                field_name=field_name,
                label_en=label_en,
                label_sw=label_sw,
                field_type=field_type,
                order=order,
                is_required=required
            )
            
            # Add options for gender dropdown
            if field_name == 'respondent_gender':
                field.options = ['Male', 'Female', 'Other', 'Prefer not to say']
                field.options_sw = ['Mwanaume', 'Mwanamke', 'Nyingine', 'Sipendelei kusema']
                field.save()
        
        self.stdout.write(self.style.SUCCESS('  ✓ Questionnaire created'))

    def create_employment_form(self):
        """Create Employment Form (Join/Leave) template"""
        self.stdout.write('Creating: Employment Form (Fomu ya Kujiungua/Kuacha Kazi)...')
        
        template = DocumentTemplate.objects.create(
            name='Employment Form - Join/Leave',
            name_sw='Fomu ya Ajira - Kujiungua/Kuacha Kazi',
            description='Form for joining or leaving employment',
            description_sw='Fomu ya kujiungua au kuacha kazi',
            category='employment',
            is_free=True,
            icon='📋',
            order=5,
            template_content_en='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Employment Form</title>
</head>
<body>
    <h1>EMPLOYMENT FORM</h1>
    
    <p><strong>Form Type:</strong> {{form_type}}</p>
    <p><strong>Date:</strong> {{form_date}}</p>
    <p><strong>Form Number:</strong> {{form_number}}</p>
    
    <h2>COMPANY INFORMATION</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Company Name:</div>
            <div class="field-value">{{company_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Department:</div>
            <div class="field-value">{{department}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">HR Contact:</div>
            <div class="field-value">{{hr_contact}}</div>
        </div>
    </div>
    
    <h2>EMPLOYEE INFORMATION</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Full Name:</div>
            <div class="field-value">{{employee_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Employee ID:</div>
            <div class="field-value">{{employee_id}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Position:</div>
            <div class="field-value">{{position}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Contact Phone:</div>
            <div class="field-value">{{employee_phone}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Email:</div>
            <div class="field-value">{{employee_email}}</div>
        </div>
    </div>
    
    <h2>FORM DETAILS</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Effective Date:</div>
            <div class="field-value">{{effective_date}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Reason:</div>
            <div class="field-value">{{reason}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Additional Notes:</div>
            <div class="field-value">{{additional_notes}}</div>
        </div>
    </div>
    
    <h2>ASSETS & CLEARANCE</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Company Assets Returned:</div>
            <div class="field-value">{{assets_returned}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Clearance Status:</div>
            <div class="field-value">{{clearance_status}}</div>
        </div>
    </div>
    
    <div class="signature-section">
        <h3>SIGNATURES</h3>
        <table>
            <tr>
                <td>
                    <div class="signature-line"></div>
                    <p>Employee Signature</p>
                    <p>Date: {{employee_sign_date}}</p>
                </td>
                <td>
                    <div class="signature-line"></div>
                    <p>HR Manager Signature</p>
                    <p>Date: {{hr_sign_date}}</p>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Generated by Pola Legal Platform on {{generated_datetime}}</p>
    </div>
</body>
</html>
            ''',
            template_content_sw='''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Fomu ya Ajira</title>
</head>
<body>
    <h1>FOMU YA AJIRA</h1>
    
    <p><strong>Aina ya Fomu:</strong> {{form_type}}</p>
    <p><strong>Tarehe:</strong> {{form_date}}</p>
    <p><strong>Namba ya Fomu:</strong> {{form_number}}</p>
    
    <h2>TAARIFA ZA KAMPUNI</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Jina la Kampuni:</div>
            <div class="field-value">{{company_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Idara:</div>
            <div class="field-value">{{department}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Mawasiliano ya HR:</div>
            <div class="field-value">{{hr_contact}}</div>
        </div>
    </div>
    
    <h2>TAARIFA ZA MWAJIRIWA</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Jina Kamili:</div>
            <div class="field-value">{{employee_name}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Namba ya Mwajiriwa:</div>
            <div class="field-value">{{employee_id}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Nafasi:</div>
            <div class="field-value">{{position}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Simu:</div>
            <div class="field-value">{{employee_phone}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Barua Pepe:</div>
            <div class="field-value">{{employee_email}}</div>
        </div>
    </div>
    
    <h2>MAELEZO YA FOMU</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Tarehe ya Kuanza Kutumika:</div>
            <div class="field-value">{{effective_date}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Sababu:</div>
            <div class="field-value">{{reason}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Maelezo Zaidi:</div>
            <div class="field-value">{{additional_notes}}</div>
        </div>
    </div>
    
    <h2>MALI NA UTOAJI RUHUSA</h2>
    <div class="section">
        <div class="field-group">
            <div class="field-label">Mali za Kampuni Zimerudishwa:</div>
            <div class="field-value">{{assets_returned}}</div>
        </div>
        <div class="field-group">
            <div class="field-label">Hali ya Utoaji Ruhusa:</div>
            <div class="field-value">{{clearance_status}}</div>
        </div>
    </div>
    
    <div class="signature-section">
        <h3>SAINI</h3>
        <table>
            <tr>
                <td>
                    <div class="signature-line"></div>
                    <p>Saini ya Mwajiriwa</p>
                    <p>Tarehe: {{employee_sign_date}}</p>
                </td>
                <td>
                    <div class="signature-line"></div>
                    <p>Saini ya Meneja wa HR</p>
                    <p>Tarehe: {{hr_sign_date}}</p>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p>Imetengenezwa na Jukwaa la Kisheria la Pola tarehe {{generated_datetime}}</p>
    </div>
</body>
</html>
            '''
        )
        
        fields = [
            ('form_type', 'Form Type', 'Aina ya Fomu', 'dropdown', 1, True),
            ('form_date', 'Form Date', 'Tarehe ya Fomu', 'date', 2, True),
            ('form_number', 'Form Number', 'Namba ya Fomu', 'text', 3, True),
            ('company_name', 'Company Name', 'Jina la Kampuni', 'text', 4, True),
            ('department', 'Department', 'Idara', 'text', 5, True),
            ('hr_contact', 'HR Contact', 'Mawasiliano ya HR', 'text', 6, True),
            ('employee_name', 'Employee Full Name', 'Jina Kamili la Mwajiriwa', 'text', 7, True),
            ('employee_id', 'Employee ID', 'Namba ya Mwajiriwa', 'text', 8, True),
            ('position', 'Position', 'Nafasi', 'text', 9, True),
            ('employee_phone', 'Employee Phone', 'Simu ya Mwajiriwa', 'phone', 10, True),
            ('employee_email', 'Employee Email', 'Barua Pepe ya Mwajiriwa', 'email', 11, True),
            ('effective_date', 'Effective Date', 'Tarehe ya Kuanza Kutumika', 'date', 12, True),
            ('reason', 'Reason', 'Sababu', 'textarea', 13, True),
            ('additional_notes', 'Additional Notes', 'Maelezo Zaidi', 'textarea', 14, False),
            ('assets_returned', 'Assets Returned', 'Mali Zimerudishwa', 'textarea', 15, False),
            ('clearance_status', 'Clearance Status', 'Hali ya Utoaji Ruhusa', 'dropdown', 16, True),
            ('employee_sign_date', 'Employee Signature Date', 'Tarehe ya Saini ya Mwajiriwa', 'date', 17, True),
            ('hr_sign_date', 'HR Signature Date', 'Tarehe ya Saini ya HR', 'date', 18, True),
        ]
        
        for field_name, label_en, label_sw, field_type, order, required in fields:
            field = TemplateField.objects.create(
                template=template,
                field_name=field_name,
                label_en=label_en,
                label_sw=label_sw,
                field_type=field_type,
                order=order,
                is_required=required
            )
            
            # Add options for dropdowns
            if field_name == 'form_type':
                field.options = ['Joining Employment', 'Leaving Employment']
                field.options_sw = ['Kujiungua Kazini', 'Kuacha Kazi']
                field.save()
            elif field_name == 'clearance_status':
                field.options = ['Pending', 'In Progress', 'Completed', 'Not Applicable']
                field.options_sw = ['Inasubiri', 'Inaendelea', 'Imekamilika', 'Haitumiki']
                field.save()
        
        self.stdout.write(self.style.SUCCESS('  ✓ Employment Form created'))
