# Generated manually to sync PaymentTransaction.payment_method choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0013_alter_consultantregistrationrequest_id_document'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenttransaction',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('Mpesa', 'Mpesa'),
                    ('Airtel', 'Airtel'),
                    ('Tigo', 'Tigo'),
                    ('Halopesa', 'Halopesa'),
                    ('Azampesa', 'Azampesa'),
                    ('CRDB', 'CRDB Bank'),
                    ('NMB', 'NMB Bank'),
                    ('bank', 'Bank Transfer'),
                ],
                max_length=50,
            ),
        ),
    ]
