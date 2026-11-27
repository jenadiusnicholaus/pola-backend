"""
Generic document template seeder.

Seeds one template directory under document_templates/templates/<slug>/
containing:

    manifest.json       template metadata (name, category, price, ...)
    template_en.html    English HTML template with {{field}} placeholders
    template_sw.html    Swahili HTML template
    fields.json         {"sections": [...], "fields": [...]} questionnaire fields

Source PDFs live in docs/_Templates/<slug>/src/ for reference only.

Usage:
    python manage.py seed_template employment-contract
    python manage.py seed_template will --dry-run
    python manage.py seed_template will --activate
"""
import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from document_templates.models import (
    DocumentTemplate,
    TemplateSection,
    TemplateField,
)

# Variables provided automatically at render time (see PDFGenerator.render_template)
BUILTIN_VARS = {'generated_date', 'generated_time', 'generated_datetime'}

PLACEHOLDER_RE = re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)')
TAG_RE = re.compile(r'{%\s*(.*?)\s*%}')
TAG_KEYWORDS = {
    'if', 'elif', 'else', 'endif', 'for', 'endfor', 'in', 'not', 'and', 'or',
    'with', 'endwith', 'as', 'is', 'none', 'true', 'false', 'empty', 'load',
    'block', 'endblock', 'extends', 'include', 'comment', 'endcomment',
}
IDENT_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')


def template_vars(html):
    """Collect variable names used in {{ var }} placeholders and {% if %} tags."""
    used = set(PLACEHOLDER_RE.findall(html))
    for tag in TAG_RE.findall(html):
        tag = re.sub(r'"[^"]*"|\'[^\']*\'', '', tag)  # drop string literals
        used.update(set(IDENT_RE.findall(tag)) - TAG_KEYWORDS)
    return used

REQUIRED_MANIFEST_KEYS = {
    'slug', 'name', 'name_sw', 'description', 'description_sw',
    'category', 'is_free', 'price', 'icon', 'order',
}

FIELD_KEYS = {
    'field_name', 'label_en', 'label_sw', 'placeholder_en', 'placeholder_sw',
    'help_text_en', 'help_text_sw', 'field_type', 'is_required', 'order',
    'validation_rules', 'options', 'options_sw', 'default_value',
}


class Command(BaseCommand):
    help = 'Seed a document template from a docs/_Templates/<slug>/ directory'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str,
                            help='Template slug or directory path (default base: document_templates/templates)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Validate only, do not write to the database')
        parser.add_argument('--activate', action='store_true',
                            help='Seed the template as active (default: inactive draft)')
        parser.add_argument('--deactivate-missing', action='store_true',
                            help='Deactivate active templates not present in document_templates/templates/')

    def handle(self, *args, **options):
        directory = Path(options['directory'])
        if not directory.is_dir():
            # Treat as a slug under document_templates/templates/
            directory = (
                Path(__file__).resolve().parents[2] / 'templates' / options['directory']
            )
        dry_run = options['dry_run']
        activate = options['activate']

        manifest = self.load_manifest(directory)
        sections, loose_fields = self.load_fields(directory)
        template_en = self.load_template(directory, 'template_en.html')
        template_sw = self.load_template(directory, 'template_sw.html')

        if not template_en and not template_sw:
            raise CommandError('Need at least one of template_en.html / template_sw.html')

        self.validate(manifest, sections, loose_fields, template_en, template_sw)

        if options['deactivate_missing']:
            self.deactivate_missing(dry_run)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run OK - no changes written'))
            return

        self.seed(manifest, sections, loose_fields, template_en, template_sw, activate)

    # ---------- loading ----------

    def load_manifest(self, directory):
        path = directory / 'manifest.json'
        if not path.exists():
            raise CommandError(f'Missing {path}')
        manifest = json.loads(path.read_text(encoding='utf-8'))
        missing = REQUIRED_MANIFEST_KEYS - manifest.keys()
        if missing:
            raise CommandError(f'manifest.json missing keys: {sorted(missing)}')
        valid_categories = {k for k, _ in DocumentTemplate.CATEGORY_CHOICES}
        if manifest['category'] not in valid_categories:
            raise CommandError(
                f"manifest.json category '{manifest['category']}' is not a valid "
                f"CATEGORY_CHOICES key ({sorted(valid_categories)})"
            )
        return manifest

    def load_fields(self, directory):
        path = directory / 'fields.json'
        if not path.exists():
            return [], []
        data = json.loads(path.read_text(encoding='utf-8'))
        return data.get('sections', []), data.get('fields', [])

    def load_template(self, directory, filename):
        path = directory / filename
        if not path.exists():
            return None
        return path.read_text(encoding='utf-8')

    # ---------- validation ----------

    def validate(self, manifest, sections, loose_fields, template_en, template_sw):
        valid_types = {k for k, _ in TemplateField.FIELD_TYPE_CHOICES}
        field_names = set()

        def check_field(field, where):
            unknown = set(field) - FIELD_KEYS
            if unknown:
                raise CommandError(f'{where}: unknown field keys {sorted(unknown)}')
            if field.get('field_type') not in valid_types:
                raise CommandError(
                    f"{where}: field '{field.get('field_name')}' has invalid "
                    f"field_type '{field.get('field_type')}' ({sorted(valid_types)})"
                )
            if field['field_name'] in field_names:
                raise CommandError(f"{where}: duplicate field_name '{field['field_name']}'")
            field_names.add(field['field_name'])

        for section in sections:
            for field in section.get('fields', []):
                check_field(field, f"section '{section.get('name')}'")
        for field in loose_fields:
            check_field(field, 'top-level fields')

        for lang, html in (('en', template_en), ('sw', template_sw)):
            if not html:
                continue
            used = template_vars(html) - BUILTIN_VARS
            missing = used - field_names
            if missing:
                raise CommandError(
                    f'template_{lang}.html uses placeholders with no matching field: '
                    f'{sorted(missing)}'
                )
            unused = field_names - used
            if unused:
                self.stdout.write(self.style.WARNING(
                    f'template_{lang}.html: fields defined but not used: {sorted(unused)}'
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Validated '{manifest['name']}': "
            f"{len(sections)} sections, {len(field_names)} fields"
        ))

    def canonical_names(self):
        """Template names declared by every manifest under templates/."""
        base = Path(__file__).resolve().parents[2] / 'templates'
        names = set()
        for path in base.glob('*/manifest.json'):
            names.add(json.loads(path.read_text(encoding='utf-8'))['name'])
        return names

    def deactivate_missing(self, dry_run):
        """Deactivate active templates whose name has no canonical manifest."""
        try:
            stale = DocumentTemplate.objects.filter(
                is_active=True,
            ).exclude(name__in=self.canonical_names())
            names = list(stale.values_list('name', flat=True))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'Could not check stale templates (DB unreachable): {e}'
            ))
            return
        if not names:
            self.stdout.write('No stale templates to deactivate')
            return
        verb = 'Would deactivate' if dry_run else 'Deactivated'
        if not dry_run:
            stale.update(is_active=False)
        self.stdout.write(self.style.WARNING(
            f'{verb} {len(names)} template(s) not in templates/: {names}'
        ))

    # ---------- seeding ----------

    @transaction.atomic
    def seed(self, manifest, sections, loose_fields, template_en, template_sw, activate):
        template, created = DocumentTemplate.objects.update_or_create(
            name=manifest['name'],
            defaults={
                'name_sw': manifest['name_sw'],
                'description': manifest['description'],
                'description_sw': manifest['description_sw'],
                'category': manifest['category'],
                'is_free': manifest['is_free'],
                'price': manifest['price'],
                'icon': manifest['icon'],
                'order': manifest['order'],
                'template_content_en': template_en or '',
                'template_content_sw': template_sw or '',
                'is_active': activate,
            },
        )

        # Deterministic rebuild: replace sections/fields with fields.json content
        template.sections.all().delete()
        template.fields.all().delete()

        count = 0
        for section_data in sections:
            section = TemplateSection.objects.create(
                template=template,
                name=section_data['name'],
                name_sw=section_data.get('name_sw', ''),
                description=section_data.get('description', ''),
                description_sw=section_data.get('description_sw', ''),
                order=section_data.get('order', 0),
            )
            for field_data in section_data.get('fields', []):
                self.create_field(template, field_data, section)
                count += 1

        for field_data in loose_fields:
            self.create_field(template, field_data, None)
            count += 1

        verb = 'Created' if created else 'Updated'
        state = 'ACTIVE' if template.is_active else 'DRAFT'
        self.stdout.write(self.style.SUCCESS(
            f'{verb} template #{template.id} "{template.name}" [{state}] '
            f'with {template.sections.count()} sections, {count} fields'
        ))

    def create_field(self, template, field_data, section):
        return TemplateField.objects.create(
            template=template,
            section=section,
            field_name=field_data['field_name'],
            label_en=field_data['label_en'],
            label_sw=field_data.get('label_sw', ''),
            placeholder_en=field_data.get('placeholder_en', ''),
            placeholder_sw=field_data.get('placeholder_sw', ''),
            help_text_en=field_data.get('help_text_en', ''),
            help_text_sw=field_data.get('help_text_sw', ''),
            field_type=field_data['field_type'],
            is_required=field_data.get('is_required', True),
            order=field_data.get('order', 0),
            validation_rules=field_data.get('validation_rules', {}),
            options=field_data.get('options', []),
            options_sw=field_data.get('options_sw', []),
            default_value=field_data.get('default_value', ''),
        )
