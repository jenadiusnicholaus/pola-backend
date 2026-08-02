# utils/email_service.py
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending HTML emails with templates"""
    
    @staticmethod
    def send_email(
        subject,
        to_email,
        template_name,
        context,
        from_email=None,
        reply_to=None
    ):
        """
        Send HTML email using template
        
        Args:
            subject: Email subject
            to_email: Recipient email address
            template_name: Template path (e.g., 'emails/otp_verification.html')
            context: Template context dictionary
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            reply_to: Reply-to email address
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Get from email from settings if not provided
            if from_email is None:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pola.co.tz')
            
            # Render HTML content
            html_content = render_to_string(template_name, context)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body='',  # Plain text will be set if needed
                from_email=from_email,
                to=[to_email],
                reply_to=[reply_to] if reply_to else None
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, 'text/html')
            
            # Send email
            email.send()
            
            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_otp_email(to_email, otp_code, expiry_minutes=10):
        """
        Send OTP verification email
        
        Args:
            to_email: Recipient email
            otp_code: 6-digit OTP code
            expiry_minutes: OTP expiry time in minutes
        
        Returns:
            bool: True if sent successfully
        """
        context = {
            'otp_code': otp_code,
            'expiry_minutes': expiry_minutes,
            'current_year': timezone.now().year,
            'app_name': getattr(settings, 'APP_NAME', 'POLA'),
        }
        
        return EmailService.send_email(
            subject=f'Your Verification Code - {context["app_name"]}',
            to_email=to_email,
            template_name='emails/otp_verification.html',
            context=context
        )
    
    @staticmethod
    def send_welcome_email(to_email, user_name):
        """
        Send welcome email to new user
        
        Args:
            to_email: Recipient email
            user_name: User's name
        
        Returns:
            bool: True if sent successfully
        """
        context = {
            'user_name': user_name,
            'current_year': timezone.now().year,
            'app_name': getattr(settings, 'APP_NAME', 'POLA'),
        }
        
        return EmailService.send_email(
            subject=f'Welcome to {context["app_name"]}!',
            to_email=to_email,
            template_name='emails/welcome.html',
            context=context
        )
    
    @staticmethod
    def send_password_reset_email(to_email, reset_link, user_name):
        """
        Send password reset email
        
        Args:
            to_email: Recipient email
            reset_link: Password reset URL
            user_name: User's name
        
        Returns:
            bool: True if sent successfully
        """
        context = {
            'user_name': user_name,
            'reset_link': reset_link,
            'current_year': timezone.now().year,
            'app_name': getattr(settings, 'APP_NAME', 'POLA'),
        }
        
        return EmailService.send_email(
            subject='Reset Your Password',
            to_email=to_email,
            template_name='emails/password_reset.html',
            context=context
        )
