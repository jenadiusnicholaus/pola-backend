# authentication/otp_service.py
import random
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache

from utils.email_service import EmailService

logger = logging.getLogger(__name__)


class OTPService:
    """Service for generating and validating OTP codes for device verification"""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(OTPService.OTP_LENGTH)])
    
    @staticmethod
    def send_otp_via_sms(phone_number, otp):
        """
        Send OTP via SMS
        TODO: Integrate with SMS provider (e.g., AzamPay, Twilio, etc.)
        For now, this is a placeholder that logs the OTP
        """
        logger.info(f"📱 OTP for {phone_number}: {otp}")
        # TODO: Implement actual SMS sending
        # Example: Use AzamPay SMS or another provider
        return True
    
    @staticmethod
    def send_otp_via_email(email, otp):
        """
        Send OTP via email
        """
        logger.info(f"📧 Sending OTP to {email}")
        return EmailService.send_otp_email(email, otp, OTPService.OTP_EXPIRY_MINUTES)
    
    @classmethod
    def generate_and_send_otp(cls, user, device, method='sms', force=False):
        """
        Generate OTP and send to user via specified method
        
        Args:
            user: User instance
            device: UserDevice instance
            method: 'sms' or 'email'
            force: If True, generate OTP even if device is already verified (for takeover)
        
        Returns:
            dict: {'success': bool, 'message': str, 'otp': str (for testing)}
        """
        # Check if device is already verified (skip if force=True for takeover)
        if device.is_verified and not force:
            return {
                'success': False,
                'message': 'Device is already verified'
            }
        
        # Check if too many failed attempts
        if device.otp_attempts >= cls.MAX_ATTEMPTS:
            return {
                'success': False,
                'message': f'Too many failed attempts. Please contact support.'
            }
        
        # Generate OTP
        otp = cls.generate_otp()
        expiry_time = timezone.now() + timedelta(minutes=cls.OTP_EXPIRY_MINUTES)
        
        # Store OTP on device
        device.verification_otp = otp
        device.otp_expires_at = expiry_time
        device.otp_attempts = 0
        device.save(update_fields=['verification_otp', 'otp_expires_at', 'otp_attempts'])
        
        # Send OTP
        sent = False
        if method == 'sms' and user.phone_number:
            sent = cls.send_otp_via_sms(user.phone_number, otp)
        elif method == 'email' and user.email:
            sent = cls.send_otp_via_email(user.email, otp)
        else:
            return {
                'success': False,
                'message': f'No {method} configured for this user'
            }
        
        if sent:
            logger.info(f"✅ OTP sent to {user.email} via {method}")
            return {
                'success': True,
                'message': f'OTP sent via {method}',
                'expires_in': cls.OTP_EXPIRY_MINUTES,
                'otp': otp  # Only for testing/dev - remove in production
            }
        else:
            return {
                'success': False,
                'message': f'Failed to send OTP via {method}'
            }
    
    @classmethod
    def validate_otp(cls, device, otp_code, force=False):
        """
        Validate OTP code for device verification
        
        Args:
            device: UserDevice instance
            otp_code: OTP code to validate
            force: If True, allow validation even if device is already verified (for takeover)
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        # Check if device is already verified (skip if force=True for takeover)
        if device.is_verified and not force:
            return {
                'success': False,
                'message': 'Device is already verified'
            }
        
        # Check if OTP exists
        if not device.verification_otp:
            return {
                'success': False,
                'message': 'No OTP has been generated for this device'
            }
        
        # Check if OTP has expired
        if device.otp_expires_at and timezone.now() > device.otp_expires_at:
            return {
                'success': False,
                'message': 'OTP has expired. Please request a new one.'
            }
        
        # Check if too many failed attempts
        if device.otp_attempts >= cls.MAX_ATTEMPTS:
            return {
                'success': False,
                'message': f'Too many failed attempts. Maximum {cls.MAX_ATTEMPTS} attempts allowed.'
            }
        
        # Validate OTP
        if device.verification_otp == otp_code:
            # Success - mark device as verified
            device.is_verified = True
            device.verification_otp = None
            device.otp_expires_at = None
            device.otp_attempts = 0
            device.save(update_fields=['is_verified', 'verification_otp', 'otp_expires_at', 'otp_attempts'])
            
            logger.info(f"✅ Device {device.device_id} verified successfully")
            return {
                'success': True,
                'message': 'Device verified successfully'
            }
        else:
            # Failed attempt
            device.otp_attempts += 1
            device.save(update_fields=['otp_attempts'])
            
            remaining_attempts = cls.MAX_ATTEMPTS - device.otp_attempts
            logger.warning(f"❌ Invalid OTP for device {device.device_id}. Attempts: {device.otp_attempts}/{cls.MAX_ATTEMPTS}")
            
            return {
                'success': False,
                'message': f'Invalid OTP. {remaining_attempts} attempts remaining.',
                'remaining_attempts': remaining_attempts
            }
