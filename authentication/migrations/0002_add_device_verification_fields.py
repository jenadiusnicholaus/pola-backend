# Generated migration for device verification fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdevice',
            name='is_verified',
            field=models.BooleanField(default=False, help_text='Device has been verified via 2FA'),
        ),
        migrations.AddField(
            model_name='userdevice',
            name='verification_otp',
            field=models.CharField(blank=True, help_text='OTP code for device verification', max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='userdevice',
            name='otp_expires_at',
            field=models.DateTimeField(blank=True, help_text='OTP expiration timestamp', null=True),
        ),
        migrations.AddField(
            model_name='userdevice',
            name='otp_attempts',
            field=models.IntegerField(default=0, help_text='Number of failed OTP attempts'),
        ),
    ]
