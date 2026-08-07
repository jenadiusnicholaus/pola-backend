from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test sending email via configured SMTP settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default=None,
            help='Recipient email address (defaults to DEFAULT_FROM_EMAIL)',
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='POLA Test Email',
            help='Email subject',
        )

    def handle(self, *args, **options):
        recipient = options['to'] or settings.DEFAULT_FROM_EMAIL
        subject = options['subject']

        self.stdout.write(self.style.HTTP_INFO(f'Sending test email to: {recipient}'))
        self.stdout.write(f'  EMAIL_BACKEND:  {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  EMAIL_HOST:     {settings.EMAIL_HOST}')
        self.stdout.write(f'  EMAIL_PORT:     {settings.EMAIL_PORT}')
        self.stdout.write(f'  EMAIL_USE_TLS:  {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write('')

        try:
            result = send_mail(
                subject=subject,
                message='This is a test email from POLA to verify SMTP configuration is working.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            if result == 1:
                self.stdout.write(self.style.SUCCESS(f'✅ Email sent successfully to {recipient}!'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Email send returned: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send email: {e}'))
