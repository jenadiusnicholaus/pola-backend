from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0003_password_reset_otp_plain'),
        ('authentication', '0003_remove_device_id_unique'),
    ]

    operations = []
