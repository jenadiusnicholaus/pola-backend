from django.db import migrations, models


class Migration(migrations.Migration):
    """Widen Document.document_type to 50 chars so admin-configured
    DocumentType codes (up to 50 chars) can be stored."""

    dependencies = [
        ('authentication', '0009_documenttype_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='document_type',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('roll_number_cert', 'Roll Number Certificate'),
                    ('practice_license', 'Practice License'),
                    ('work_certificate', 'Certificate of Work'),
                    ('professional_cert', 'Professional Certificate'),
                    ('employment_letter', 'Employment Letter'),
                    ('organization_cert', 'Organization Certificate'),
                    ('business_license', 'Business License'),
                    ('registration_cert', 'Registration Certificate'),
                    ('firm_documents', 'Other Firm Documents'),
                    ('id_document', 'ID Document'),
                    ('academic', 'Academic Certificate'),
                    ('other', 'Other Document'),
                    ('registration', 'Registration Certificate'),
                    ('practice', 'Practice License'),
                ],
            ),
        ),
    ]
