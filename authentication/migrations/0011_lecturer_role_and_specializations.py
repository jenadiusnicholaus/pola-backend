from django.db import migrations


LECTURER_DESCRIPTION_EN = (
    'An academic professional who teaches law courses at universities '
    'or legal training institutions.'
)
LECTURER_DESCRIPTION_SW = (
    'Mtaalamu wa kitaaluma anayefundisha masomo ya sheria katika vyuo '
    'vikuu au taasisi za mafunzo ya kisheria.'
)

SPECIALIZATIONS = [
    ('Administrative Law', 'Sheria za Utawala',
     'Legal practice focusing on government administration and regulatory matters'),
    ('Contract Law', 'Sheria za Mikataba',
     'Legal practice focusing on drafting, interpreting, and enforcing contracts'),
    ('Civil Litigation', 'Mashauri ya Madai',
     'Legal practice focusing on representing clients in civil disputes and lawsuits'),
    ('Probate Law', 'Sheria za Mirathi',
     'Legal practice focusing on estates, wills, and inheritance matters'),
    ('Labour and Employment Law', 'Sheria za Kazi na Ajira',
     'Legal practice focusing on employment and labour relations'),
    ('Banking and Finance Law', 'Sheria za Benki na Fedha',
     'Legal practice focusing on banking, finance, and financial services regulation'),
    ('Insurance Law', 'Sheria za Bima',
     'Legal practice focusing on insurance policies, claims, and regulation'),
    ('Mining and Natural Resources Law', 'Sheria za Madini na Maliasili',
     'Legal practice focusing on mining, natural resources, and extractive industries'),
    ('Cyber Law', 'Sheria za Mtandao',
     'Legal practice focusing on internet, digital, and information technology matters'),
    ('International Law', 'Sheria za Kimataifa',
     'Legal practice focusing on treaties, cross-border matters, and international relations'),
]


def seed_lecturer_role(apps, schema_editor):
    UserRole = apps.get_model('authentication', 'UserRole')
    UserRole.objects.get_or_create(
        role_name='lecturer',
        defaults={
            'description_en': LECTURER_DESCRIPTION_EN,
            'description_sw': LECTURER_DESCRIPTION_SW,
        },
    )


def seed_specializations(apps, schema_editor):
    Specialization = apps.get_model('authentication', 'Specialization')

    # Rename legacy "Labor Law" only if the new name doesn't already exist
    if not Specialization.objects.filter(name_en='Labour and Employment Law').exists():
        Specialization.objects.filter(name_en='Labor Law').update(
            name_en='Labour and Employment Law',
            name_sw='Sheria za Kazi na Ajira',
        )

    for name_en, name_sw, description in SPECIALIZATIONS:
        Specialization.objects.get_or_create(
            name_en=name_en,
            defaults={'name_sw': name_sw, 'description': description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0010_alter_document_document_type'),
    ]

    operations = [
        migrations.RunPython(seed_lecturer_role, migrations.RunPython.noop),
        migrations.RunPython(seed_specializations, migrations.RunPython.noop),
    ]
