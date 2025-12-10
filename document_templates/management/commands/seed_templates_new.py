"""
Django management command to seed document templates from Word documents

Usage:
    python manage.py seed_templates_new
    python manage.py seed_templates_new --clear  # Clear existing templates first
"""
from django.core.management.base import BaseCommand
from document_templates.models import (
    DocumentTemplate,
    TemplateSection,
    TemplateField
)
import os


class Command(BaseCommand):
    help = 'Seeds document templates from extracted Word documents'

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

        self.stdout.write('Seeding document templates from Word documents...\n')

        # Load templates from extracted Word documents
        templates_created = 0
        
        # 1. Employment Contract
        if self.create_employment_contract():
            templates_created += 1
        
        # 2. Resignation Letter
        if self.create_resignation_letter():
            templates_created += 1
        
        # 3. Notice
        if self.create_notice():
            templates_created += 1
        
        # 4. Questionnaire
        if self.create_questionnaire():
            templates_created += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {templates_created} templates!'))
        self.stdout.write(self.style.SUCCESS(f'Total templates in database: {DocumentTemplate.objects.count()}'))

    def create_employment_contract(self):
        """Create Employment Contract template from Word document"""
        self.stdout.write('Creating: Employment Contract...')
        
        # Load the actual Word document template
        template_content_en = self.load_template_file('iii._employment_contract.html')
        
        if not template_content_en:
            self.stdout.write(self.style.ERROR('✗ Failed - template file not found'))
            return False
        
        template = DocumentTemplate.objects.create(
            name='Employment Contract',
            name_sw='Mkataba wa Ajira',
            description='Official employment contract document extracted from Word template',
            description_sw='Mkataba rasmi wa ajira uliochukuliwa kutoka kwenye template ya Word',
            category='employment',
            is_free=True,
            icon='📄',
            order=1,
            template_content_en=template_content_en,
            template_content_sw=template_content_en  # Use same template, fields will be in Swahili when needed
        )
        
        # Create sections and fields based on the Word document structure
        # Personal Info Section
        personal_section = TemplateSection.objects.create(
            template=template,
            name='Contract Date',
            name_sw='Tarehe ya Mkataba',
            order=1
        )
        
        TemplateField.objects.create(
            template=template,
            section=personal_section,
            name='contract_date_day',
            label='Contract Day',
            label_sw='Siku ya Mkataba',
            field_type='text',
            is_required=True,
            order=1
        )
        
        TemplateField.objects.create(
            template=template,
            section=personal_section,
            name='contract_date_month',
            label='Contract Month',
            label_sw='Mwezi wa Mkataba',
            field_type='text',
            is_required=True,
            order=2
        )
        
        TemplateField.objects.create(
            template=template,
            section=personal_section,
            name='contract_date_year',
            label='Contract Year',
            label_sw='Mwaka wa Mkataba',
            field_type='text',
            is_required=True,
            order=3
        )
        
        # Employer Section
        employer_section = TemplateSection.objects.create(
            template=template,
            name='Employer Information',
            name_sw='Taarifa za Mwajiri',
            order=2
        )
        
        TemplateField.objects.create(
            template=template,
            section=employer_section,
            name='employer_name',
            label='Employer Name',
            label_sw='Jina la Mwajiri',
            field_type='text',
            is_required=True,
            order=1
        )
        
        TemplateField.objects.create(
            template=template,
            section=employer_section,
            name='employer_address_street',
            label='Employer Street Address',
            label_sw='Anwani ya Barabara ya Mwajiri',
            field_type='text',
            is_required=True,
            order=2
        )
        
        TemplateField.objects.create(
            template=template,
            section=employer_section,
            name='employer_address_city',
            label='Employer City',
            label_sw='Jiji la Mwajiri',
            field_type='text',
            is_required=True,
            order=3
        )
        
        TemplateField.objects.create(
            template=template,
            section=employer_section,
            name='employer_phone',
            label='Employer Phone',
            label_sw='Simu ya Mwajiri',
            field_type='text',
            is_required=True,
            order=4
        )
        
        TemplateField.objects.create(
            template=template,
            section=employer_section,
            name='employer_email',
            label='Employer Email',
            label_sw='Barua Pepe ya Mwajiri',
            field_type='email',
            is_required=True,
            order=5
        )
        
        # Employee Section
        employee_section = TemplateSection.objects.create(
            template=template,
            name='Employee Information',
            name_sw='Taarifa za Mwajiriwa',
            order=3
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_name',
            label='Employee Full Name',
            label_sw='Jina Kamili la Mwajiriwa',
            field_type='text',
            is_required=True,
            order=1
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_address_street',
            label='Employee Street Address',
            label_sw='Anwani ya Barabara ya Mwajiriwa',
            field_type='text',
            is_required=True,
            order=2
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_address_city',
            label='Employee City',
            label_sw='Jiji la Mwajiriwa',
            field_type='text',
            is_required=True,
            order=3
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_phone',
            label='Employee Phone',
            label_sw='Simu ya Mwajiriwa',
            field_type='text',
            is_required=True,
            order=4
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_id_type',
            label='ID Type',
            label_sw='Aina ya Kitambulisho',
            field_type='select',
            is_required=True,
            validation_rules={'choices': ['National ID', 'Passport', 'Driving License']},
            order=5
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_id_number',
            label='ID Number',
            label_sw='Namba ya Kitambulisho',
            field_type='text',
            is_required=True,
            order=6
        )
        
        TemplateField.objects.create(
            template=template,
            section=employee_section,
            name='employee_email',
            label='Employee Email',
            label_sw='Barua Pepe ya Mwajiriwa',
            field_type='email',
            is_required=False,
            order=7
        )
        
        # Employment Details Section
        employment_section = TemplateSection.objects.create(
            template=template,
            name='Employment Details',
            name_sw='Maelezo ya Ajira',
            order=4
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='employment_start_day',
            label='Employment Start Day',
            label_sw='Siku ya Kuanza Kazi',
            field_type='text',
            is_required=True,
            order=1
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='employment_start_month',
            label='Employment Start Month',
            label_sw='Mwezi wa Kuanza Kazi',
            field_type='text',
            is_required=True,
            order=2
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='employment_start_year',
            label='Employment Start Year',
            label_sw='Mwaka wa Kuanza Kazi',
            field_type='text',
            is_required=True,
            order=3
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='employment_end_day',
            label='Employment End Day (if fixed term)',
            label_sw='Siku ya Kumalizika (kama ni muda maalum)',
            field_type='text',
            is_required=False,
            order=4
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='employment_end_month',
            label='Employment End Month (if fixed term)',
            label_sw='Mwezi wa Kumalizika (kama ni muda maalum)',
            field_type='text',
            is_required=False,
            order=5
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='employment_end_year',
            label='Employment End Year (if fixed term)',
            label_sw='Mwaka wa Kumalizika (kama ni muda maalum)',
            field_type='text',
            is_required=False,
            order=6
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='workplace_location',
            label='Workplace Location',
            label_sw='Mahali pa Kazi',
            field_type='text',
            is_required=True,
            order=7
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='job_title',
            label='Job Title/Position',
            label_sw='Cheo/Nafasi',
            field_type='text',
            is_required=True,
            order=8
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='salary_amount',
            label='Salary Amount',
            label_sw='Kiasi cha Mshahara',
            field_type='number',
            is_required=True,
            order=9
        )
        
        TemplateField.objects.create(
            template=template,
            section=employment_section,
            name='salary_period',
            label='Salary Period',
            label_sw='Kipindi cha Mshahara',
            field_type='select',
            validation_rules={'choices': ['Monthly', 'Weekly', 'Daily']},
            is_required=True,
            order=10
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Created Employment Contract with 19 fields'))
        return True

    def create_resignation_letter(self):
        """Create Resignation Letter template"""
        self.stdout.write('Creating: Resignation Letter...')
        
        # Load English version
        template_content_en = self.load_template_file('iii._resignation_letter.html')
        # Load Swahili version
        template_content_sw = self.load_template_file('i._barua_ya_kujiuzulu_au_kuacha_kazi.html')
        
        if not template_content_en or not template_content_sw:
            self.stdout.write(self.style.ERROR('✗ Failed - template file not found'))
            return False
        
        template = DocumentTemplate.objects.create(
            name='Resignation Letter',
            name_sw='Barua ya Kujiuzulu',
            description='Official resignation letter document',
            description_sw='Barua rasmi ya kujiuzulu',
            category='resignation',
            is_free=True,
            icon='✉️',
            order=2,
            template_content_en=template_content_en,
            template_content_sw=template_content_sw
        )
        
        # TODO: Add fields based on resignation letter structure
        # This would need analysis of the resignation letter template
        
        self.stdout.write(self.style.SUCCESS('✓ Created Resignation Letter'))
        return True

    def create_notice(self):
        """Create Notice template"""
        self.stdout.write('Creating: Notice...')
        
        template_content_en = self.load_template_file('iii._notice_(english).html')
        
        if not template_content_en:
            self.stdout.write(self.style.ERROR('✗ Failed - template file not found'))
            return False
        
        template = DocumentTemplate.objects.create(
            name='Official Notice',
            name_sw='Ilani Rasmi',
            description='Official notice document',
            description_sw='Waraka rasmi wa ilani',
            category='notice',
            is_free=True,
            icon='📢',
            order=3,
            template_content_en=template_content_en,
            template_content_sw=template_content_en
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Created Notice'))
        return True

    def create_questionnaire(self):
        """Create Questionnaire template"""
        self.stdout.write('Creating: Questionnaire...')
        
        # Load English and Swahili versions
        template_content_en = self.load_template_file('iv._questionnaire_(english).html')
        template_content_sw = self.load_template_file('ii._questionnaire_(kiswahili).html')
        
        if not template_content_en or not template_content_sw:
            self.stdout.write(self.style.ERROR('✗ Failed - template file not found'))
            return False
        
        template = DocumentTemplate.objects.create(
            name='Employment Questionnaire',
            name_sw='Dodoso la Ajira',
            description='Employment questionnaire form',
            description_sw='Fomu ya dodoso la ajira',
            category='form',
            is_free=True,
            icon='📋',
            order=4,
            template_content_en=template_content_en,
            template_content_sw=template_content_sw
        )
        
        self.stdout.write(self.style.SUCCESS('✓ Created Questionnaire'))
        return True
