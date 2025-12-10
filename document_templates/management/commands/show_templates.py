"""
Django management command to view document templates

Usage:
    python manage.py show_templates              # List all templates
    python manage.py show_templates --id 1       # Show specific template with fields
    python manage.py show_templates --category employment
    python manage.py show_templates --stats      # Show statistics
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from document_templates.models import DocumentTemplate, TemplateField, UserDocument
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)


class Command(BaseCommand):
    help = 'View document templates and their details'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            help='Show specific template by ID',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Filter by category (employment, legal_notice, resignation, questionnaire, general)',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show template statistics',
        )
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            choices=['en', 'sw'],
            help='Language for display (en or sw)',
        )

    def handle(self, *args, **options):
        template_id = options.get('id')
        category = options.get('category')
        show_stats = options.get('stats')
        language = options.get('language')

        if show_stats:
            self.show_statistics()
        elif template_id:
            self.show_template_detail(template_id, language)
        else:
            self.list_templates(category, language)

    def list_templates(self, category=None, language='en'):
        """List all templates"""
        self.stdout.write(f"\n{Fore.CYAN}{'='*80}")
        self.stdout.write(f"{Fore.CYAN}{'DOCUMENT TEMPLATES':^80}")
        self.stdout.write(f"{Fore.CYAN}{'='*80}\n")

        templates = DocumentTemplate.objects.all()
        
        if category:
            templates = templates.filter(category=category)
        
        if not templates.exists():
            self.stdout.write(f"{Fore.YELLOW}No templates found.")
            return

        templates = templates.order_by('category', 'order')

        for template in templates:
            name = template.name_sw if language == 'sw' else template.name
            desc = template.description_sw if language == 'sw' else template.description
            
            # Status indicator
            status = f"{Fore.GREEN}●" if template.is_active else f"{Fore.RED}●"
            
            # Price
            if template.is_free:
                price = f"{Fore.GREEN}FREE" if language == 'en' else f"{Fore.GREEN}BURE"
            else:
                price = f"{Fore.YELLOW}TSh {template.price:,.0f}"

            self.stdout.write(f"\n{status} {Fore.WHITE}{Style.BRIGHT}[{template.id}] {name}")
            self.stdout.write(f"   {Fore.CYAN}Category: {Fore.WHITE}{template.get_category_display()}")
            self.stdout.write(f"   {Fore.CYAN}Price: {price}")
            self.stdout.write(f"   {Fore.CYAN}Fields: {Fore.WHITE}{template.fields.count()}")
            self.stdout.write(f"   {Fore.CYAN}Usage: {Fore.WHITE}{template.usage_count} times")
            self.stdout.write(f"   {Fore.CYAN}Icon: {template.icon or '📄'}")
            
            if desc and len(desc) <= 100:
                self.stdout.write(f"   {Fore.MAGENTA}{desc}")
            elif desc:
                self.stdout.write(f"   {Fore.MAGENTA}{desc[:100]}...")

        self.stdout.write(f"\n{Fore.CYAN}{'='*80}")
        self.stdout.write(f"{Fore.GREEN}Total templates: {templates.count()}")
        self.stdout.write(f"{Fore.CYAN}{'='*80}\n")
        
        self.stdout.write(f"\n{Fore.YELLOW}💡 Use --id <ID> to see template details with fields")
        self.stdout.write(f"{Fore.YELLOW}💡 Use --stats to see statistics\n")

    def show_template_detail(self, template_id, language='en'):
        """Show detailed template information with fields"""
        try:
            template = DocumentTemplate.objects.prefetch_related(
                'sections__fields',
                'fields'
            ).get(id=template_id)
        except DocumentTemplate.DoesNotExist:
            self.stdout.write(f"{Fore.RED}Template with ID {template_id} not found.")
            return

        name = template.name_sw if language == 'sw' else template.name
        desc = template.description_sw if language == 'sw' else template.description

        self.stdout.write(f"\n{Fore.CYAN}{'='*80}")
        self.stdout.write(f"{Fore.CYAN}{name.upper():^80}")
        self.stdout.write(f"{Fore.CYAN}{'='*80}\n")

        # Basic info
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Template ID: {Fore.YELLOW}{template.id}")
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Category: {Fore.CYAN}{template.get_category_display()}")
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Status: {Fore.GREEN if template.is_active else Fore.RED}{'Active' if template.is_active else 'Inactive'}")
        
        if template.is_free:
            self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Price: {Fore.GREEN}FREE")
        else:
            self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Price: {Fore.YELLOW}TSh {template.price:,.0f}")
        
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Usage Count: {Fore.CYAN}{template.usage_count} times")
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Icon: {template.icon or '📄'}")
        self.stdout.write(f"\n{Fore.MAGENTA}{desc}\n")

        # Sections and fields
        sections = template.sections.all().order_by('order')
        
        if sections.exists():
            self.stdout.write(f"{Fore.CYAN}{'-'*80}")
            self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}SECTIONS & FIELDS")
            self.stdout.write(f"{Fore.CYAN}{'-'*80}\n")
            
            for section in sections:
                section_name = section.name_sw if language == 'sw' else section.name
                self.stdout.write(f"\n{Fore.YELLOW}{Style.BRIGHT}📋 {section_name} (Section {section.order})")
                
                fields = section.fields.all().order_by('order')
                for field in fields:
                    self._print_field(field, language, indent=3)
        
        # Fields without sections
        fields_without_section = template.fields.filter(section__isnull=True).order_by('order')
        if fields_without_section.exists():
            self.stdout.write(f"\n{Fore.CYAN}{'-'*80}")
            self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}OTHER FIELDS")
            self.stdout.write(f"{Fore.CYAN}{'-'*80}\n")
            
            for field in fields_without_section:
                self._print_field(field, language, indent=0)

        # Total counts
        total_fields = template.fields.count()
        required_fields = template.fields.filter(is_required=True).count()
        
        self.stdout.write(f"\n{Fore.CYAN}{'-'*80}")
        self.stdout.write(f"{Fore.GREEN}Total Fields: {total_fields}")
        self.stdout.write(f"{Fore.GREEN}Required Fields: {required_fields}")
        self.stdout.write(f"{Fore.GREEN}Optional Fields: {total_fields - required_fields}")
        self.stdout.write(f"{Fore.CYAN}{'-'*80}\n")

    def _print_field(self, field, language='en', indent=0):
        """Print field details"""
        label = field.label_sw if language == 'sw' else field.label_en
        placeholder = field.placeholder_sw if language == 'sw' else field.placeholder_en
        help_text = field.help_text_sw if language == 'sw' else field.help_text_en
        
        indent_str = "   " * indent
        required = f"{Fore.RED}*" if field.is_required else f"{Fore.GREEN}○"
        
        self.stdout.write(f"\n{indent_str}{required} {Fore.WHITE}{Style.BRIGHT}{label}")
        self.stdout.write(f"{indent_str}   {Fore.CYAN}Field: {Fore.WHITE}{field.field_name}")
        self.stdout.write(f"{indent_str}   {Fore.CYAN}Type: {Fore.YELLOW}{field.field_type}")
        self.stdout.write(f"{indent_str}   {Fore.CYAN}Required: {Fore.WHITE}{'Yes' if field.is_required else 'No'}")
        
        if placeholder:
            self.stdout.write(f"{indent_str}   {Fore.CYAN}Placeholder: {Fore.MAGENTA}{placeholder}")
        
        if help_text:
            self.stdout.write(f"{indent_str}   {Fore.CYAN}Help: {Fore.MAGENTA}{help_text}")
        
        if field.options:
            options_str = ", ".join(str(opt) for opt in field.options[:5])
            if len(field.options) > 5:
                options_str += f" ... (+{len(field.options) - 5} more)"
            self.stdout.write(f"{indent_str}   {Fore.CYAN}Options: {Fore.WHITE}{options_str}")
        
        if field.validation_rules:
            rules = []
            for key, value in field.validation_rules.items():
                rules.append(f"{key}={value}")
            self.stdout.write(f"{indent_str}   {Fore.CYAN}Validation: {Fore.WHITE}{', '.join(rules)}")

    def show_statistics(self):
        """Show template statistics"""
        self.stdout.write(f"\n{Fore.CYAN}{'='*80}")
        self.stdout.write(f"{Fore.CYAN}{'TEMPLATE STATISTICS':^80}")
        self.stdout.write(f"{Fore.CYAN}{'='*80}\n")

        # Total templates
        total_templates = DocumentTemplate.objects.count()
        active_templates = DocumentTemplate.objects.filter(is_active=True).count()
        inactive_templates = total_templates - active_templates
        
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Total Templates: {Fore.CYAN}{total_templates}")
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Active: {Fore.GREEN}{active_templates}")
        self.stdout.write(f"{Fore.WHITE}{Style.BRIGHT}Inactive: {Fore.RED}{inactive_templates}\n")

        # By category
        self.stdout.write(f"{Fore.YELLOW}{Style.BRIGHT}Templates by Category:")
        categories = DocumentTemplate.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for cat in categories:
            category_display = dict(DocumentTemplate.CATEGORY_CHOICES).get(
                cat['category'], cat['category']
            )
            self.stdout.write(f"  {Fore.CYAN}• {category_display}: {Fore.WHITE}{cat['count']}")

        # Free vs Paid
        free_templates = DocumentTemplate.objects.filter(is_free=True).count()
        paid_templates = total_templates - free_templates
        
        self.stdout.write(f"\n{Fore.YELLOW}{Style.BRIGHT}Pricing:")
        self.stdout.write(f"  {Fore.GREEN}• Free: {free_templates}")
        self.stdout.write(f"  {Fore.YELLOW}• Paid: {paid_templates}")

        # Usage statistics
        total_usage = DocumentTemplate.objects.aggregate(
            total=Count('user_documents')
        )['total'] or 0
        
        most_used = DocumentTemplate.objects.annotate(
            docs_count=Count('user_documents')
        ).order_by('-docs_count').first()

        self.stdout.write(f"\n{Fore.YELLOW}{Style.BRIGHT}Usage:")
        self.stdout.write(f"  {Fore.CYAN}• Total Generated Documents: {Fore.WHITE}{total_usage}")
        
        if most_used and most_used.docs_count > 0:
            self.stdout.write(f"  {Fore.CYAN}• Most Used Template: {Fore.WHITE}{most_used.name} ({most_used.docs_count} docs)")

        # Field statistics
        total_fields = TemplateField.objects.count()
        required_fields = TemplateField.objects.filter(is_required=True).count()
        
        self.stdout.write(f"\n{Fore.YELLOW}{Style.BRIGHT}Fields:")
        self.stdout.write(f"  {Fore.CYAN}• Total Fields: {Fore.WHITE}{total_fields}")
        self.stdout.write(f"  {Fore.CYAN}• Required Fields: {Fore.WHITE}{required_fields}")
        self.stdout.write(f"  {Fore.CYAN}• Optional Fields: {Fore.WHITE}{total_fields - required_fields}")

        # Field types
        field_types = TemplateField.objects.values('field_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        if field_types:
            self.stdout.write(f"\n{Fore.YELLOW}{Style.BRIGHT}Top Field Types:")
            for ft in field_types:
                self.stdout.write(f"  {Fore.CYAN}• {ft['field_type']}: {Fore.WHITE}{ft['count']}")

        # User documents statistics
        total_docs = UserDocument.objects.count()
        completed_docs = UserDocument.objects.filter(status='completed').count()
        failed_docs = UserDocument.objects.filter(status='failed').count()

        self.stdout.write(f"\n{Fore.YELLOW}{Style.BRIGHT}Generated Documents:")
        self.stdout.write(f"  {Fore.CYAN}• Total: {Fore.WHITE}{total_docs}")
        self.stdout.write(f"  {Fore.GREEN}• Completed: {completed_docs}")
        self.stdout.write(f"  {Fore.RED}• Failed: {failed_docs}")

        self.stdout.write(f"\n{Fore.CYAN}{'='*80}\n")
