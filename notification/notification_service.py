"""
Unified Notification Service

Central service for sending all types of notifications across the platform.
Handles FCM push notifications with proper error handling and logging.
"""

import logging
from typing import Dict, Optional, List
from django.utils import timezone
from authentication.models import PolaUser
from authentication.device_models import UserDevice
from .google_firebase_service.push_notification.auth_api import GoogleAuth
from .google_firebase_service.push_notification.fcm_api import FCM

logger = logging.getLogger(__name__)


class NotificationService:
    """Unified service for sending push notifications"""
    
    @staticmethod
    def _get_fcm_instance():
        """Get FCM instance with access token - reads project_id from service account file"""
        try:
            google_auth = GoogleAuth()  # Auto-reads project_id from service_account_file.json
            access_token = google_auth.get_access_token()
            project_id = google_auth.get_project_id()
            return FCM(project_id, access_token)
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {str(e)}")
            return None
    
    @staticmethod
    def _get_user_devices(user: PolaUser) -> List[UserDevice]:
        """Get active devices with FCM tokens for a user"""
        return UserDevice.objects.filter(
            user=user,
            is_current_device=True,
            is_active=True,
            fcm_token__isnull=False
        ).exclude(fcm_token='')
    
    @staticmethod
    def send_notification_to_user(
        user: PolaUser,
        title: str,
        body: str,
        data: Dict,
        notification_type: str = 'general',
        priority: str = 'high'
    ) -> bool:
        """
        Send notification to a user's devices
        
        Args:
            user: PolaUser to notify
            title: Notification title
            body: Notification body text
            data: Additional data payload (must be dict with string values)
            notification_type: Type for categorization (mention, reply, consultation, payment, etc.)
            priority: 'high' or 'normal'
        
        Returns:
            bool: True if at least one notification sent successfully
        """
        # Save notification to database first
        from .models import UserNotification
        
        logger.info(f"📤 Creating notification for user {user.id} ({user.email}): {title}")
        
        notification_record = UserNotification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
            fcm_sent=False  # Will update after FCM send
        )
        
        logger.info(f"📝 Notification record created: ID={notification_record.id}")
        
        devices = NotificationService._get_user_devices(user)
        
        if not devices.exists():
            logger.warning(f"⚠️ No active devices with FCM token found for user {user.id} ({user.email})")
            logger.warning(f"   User needs to: 1) Log in on app 2) Accept notification permission 3) Device must register FCM token")
            return False
        
        logger.info(f"📱 Found {devices.count()} active device(s) for user {user.email}")
        
        fcm = NotificationService._get_fcm_instance()
        if not fcm:
            logger.error(f"❌ Failed to initialize FCM client")
            return False
        
        # Ensure all data values are strings
        data_payload = {k: str(v) for k, v in data.items()}
        data_payload['type'] = notification_type
        data_payload['timestamp'] = str(int(timezone.now().timestamp() * 1000))
        
        successful_sends = 0
        
        for device in devices:
            try:
                status_code, response = fcm.send_notification(
                    device.fcm_token,
                    title,
                    body,
                    data_payload
                )
                
                if status_code == 200:
                    successful_sends += 1
                    logger.info(f"✅ Notification sent to {user.email} - Device: {device.device_name or device.device_id[:8]}")
                else:
                    logger.error(f"❌ FCM failed for {user.email}: {response}")
            
            except Exception as e:
                logger.error(f"❌ Error sending notification to {user.email}: {str(e)}")
                continue
        
        # Update notification record
        if successful_sends > 0:
            notification_record.fcm_sent = True
            notification_record.save(update_fields=['fcm_sent'])
        
        return successful_sends > 0
    
    @staticmethod
    def send_mention_notification(
        mentioned_user: PolaUser,
        mentioning_user: PolaUser,
        comment_id: int,
        content_id: int,
        hub_type: str,
        comment_preview: str
    ) -> bool:
        """
        Send notification when user is mentioned in a comment
        
        Args:
            mentioned_user: User who was mentioned
            mentioning_user: User who mentioned them
            comment_id: ID of comment containing mention
            content_id: ID of the post/content
            hub_type: Type of hub (forum, advocates, students, etc.)
            comment_preview: Preview text of the comment
        """
        # Check if user has notifications enabled for mentions
        try:
            privacy_settings = mentioned_user.privacy_settings
            if not privacy_settings.notify_on_tag:
                logger.info(f"User {mentioned_user.email} has mention notifications disabled")
                return False
        except Exception:
            # If no privacy settings, default to sending
            pass
        
        title = f"{mentioning_user.get_full_name() or mentioning_user.email} mentioned you"
        body = f"in a comment: {comment_preview[:100]}"
        
        data = {
            'action_type': 'open_comment',
            'comment_id': comment_id,
            'content_id': content_id,
            'hub_type': hub_type,
            'mentioned_by_id': mentioning_user.id,
            'mentioned_by_name': mentioning_user.get_full_name() or mentioning_user.email,
            'comment_preview': comment_preview[:200]
        }
        
        return NotificationService.send_notification_to_user(
            user=mentioned_user,
            title=title,
            body=body,
            data=data,
            notification_type='mention',
            priority='high'
        )
    
    @staticmethod
    def send_reply_notification(
        parent_comment_author: PolaUser,
        replying_user: PolaUser,
        comment_id: int,
        parent_comment_id: int,
        content_id: int,
        hub_type: str,
        reply_preview: str
    ) -> bool:
        """
        Send notification when someone replies to your comment
        
        Args:
            parent_comment_author: Author of the parent comment
            replying_user: User who replied
            comment_id: ID of the reply comment
            parent_comment_id: ID of parent comment
            content_id: ID of the post/content
            hub_type: Type of hub
            reply_preview: Preview text of the reply
        """
        # Don't notify if replying to own comment
        if parent_comment_author.id == replying_user.id:
            return False
        
        title = f"{replying_user.get_full_name() or replying_user.email} replied to your comment"
        body = reply_preview[:150]
        
        data = {
            'action_type': 'open_comment',
            'comment_id': comment_id,
            'parent_comment_id': parent_comment_id,
            'content_id': content_id,
            'hub_type': hub_type,
            'replied_by_id': replying_user.id,
            'replied_by_name': replying_user.get_full_name() or replying_user.email,
            'reply_preview': reply_preview[:200]
        }
        
        return NotificationService.send_notification_to_user(
            user=parent_comment_author,
            title=title,
            body=body,
            data=data,
            notification_type='reply',
            priority='high'
        )
    
    @staticmethod
    def send_consultation_request_notification(
        consultant: PolaUser,
        client: PolaUser,
        booking_id: int,
        consultation_type: str,
        scheduled_date: str,
        scheduled_time: str
    ) -> bool:
        """
        Send notification to ADMINS when client books a consultation
        
        Args:
            consultant: Professional being booked (included in notification info)
            client: Client who booked
            booking_id: ID of ConsultationBooking
            consultation_type: physical, mobile, video
            scheduled_date: Date string
            scheduled_time: Time string
        """
        consultant_name = consultant.get_full_name() or consultant.email
        client_name = client.get_full_name() or client.email
        
        title = f"New consultation request"
        body = f"{client_name} booked {consultation_type} consultation with {consultant_name} on {scheduled_date} at {scheduled_time}"
        
        data = {
            'action_type': 'open_consultation',
            'booking_id': booking_id,
            'client_id': client.id,
            'client_name': client_name,
            'consultant_id': consultant.id,
            'consultant_name': consultant_name,
            'consultation_type': consultation_type,
            'scheduled_date': scheduled_date,
            'scheduled_time': scheduled_time
        }
        
        # Send to all admin users
        admins = PolaUser.objects.filter(is_staff=True, is_active=True)
        
        if not admins.exists():
            logger.warning("No admin users found to send consultation request notification")
            return False
        
        successful_sends = 0
        for admin in admins:
            result = NotificationService.send_notification_to_user(
                user=admin,
                title=title,
                body=body,
                data=data,
                notification_type='consultation_request',
                priority='high'
            )
            if result:
                successful_sends += 1
        
        logger.info(f"Consultation request notification sent to {successful_sends}/{admins.count()} admins")
        return successful_sends > 0
    
    @staticmethod
    def send_payment_received_notification(
        recipient: PolaUser,
        payer: PolaUser,
        amount: str,
        currency: str,
        payment_id: int,
        service_type: str
    ) -> bool:
        """
        Send notification when professional receives payment
        
        Args:
            recipient: User receiving the payment
            payer: User who made the payment
            amount: Payment amount
            currency: Currency code (TZS, USD, etc.)
            payment_id: ID of PaymentTransaction
            service_type: consultation, document, subscription, etc.
        """
        title = f"Payment received: {currency} {amount}"
        body = f"from {payer.get_full_name() or payer.email} for {service_type}"
        
        data = {
            'action_type': 'open_earnings',
            'payment_id': payment_id,
            'amount': amount,
            'currency': currency,
            'from_user_id': payer.id,
            'from_user_name': payer.get_full_name() or payer.email,
            'service_type': service_type
        }
        
        return NotificationService.send_notification_to_user(
            user=recipient,
            title=title,
            body=body,
            data=data,
            notification_type='payment_received',
            priority='high'
        )
    
    @staticmethod
    def send_consultation_status_notification(
        client: PolaUser,
        consultant: PolaUser,
        booking_id: int,
        status: str,
        scheduled_date: str
    ) -> bool:
        """
        Send notification when consultation status changes
        
        Args:
            client: Client who booked
            consultant: Professional
            booking_id: ID of ConsultationBooking
            status: confirmed, cancelled, completed
            scheduled_date: Date string
        """
        status_messages = {
            'confirmed': f"Your consultation with {consultant.get_full_name() or consultant.email} is confirmed",
            'cancelled': f"Your consultation with {consultant.get_full_name() or consultant.email} was cancelled",
            'completed': f"Your consultation with {consultant.get_full_name() or consultant.email} is complete"
        }
        
        title = status_messages.get(status, "Consultation update")
        body = f"Scheduled for {scheduled_date}"
        
        data = {
            'action_type': 'open_consultation',
            'booking_id': booking_id,
            'status': status,
            'consultant_name': consultant.get_full_name() or consultant.email,
            'scheduled_date': scheduled_date
        }
        
        return NotificationService.send_notification_to_user(
            user=client,
            title=title,
            body=body,
            data=data,
            notification_type='consultation_status',
            priority='high' if status == 'confirmed' else 'normal'
        )
    
    @staticmethod
    def send_document_ready_notification(
        user: PolaUser,
        document_id: int,
        document_title: str,
        document_type: str
    ) -> bool:
        """
        Send notification when purchased/generated document is ready
        
        Args:
            user: User who purchased/generated the document
            document_id: ID of the document
            document_title: Title/name of document
            document_type: contract, notice, resignation, etc.
        """
        title = f"Your {document_title} is ready"
        body = "Tap to download"
        
        data = {
            'action_type': 'open_document',
            'document_id': document_id,
            'document_title': document_title,
            'document_type': document_type
        }
        
        return NotificationService.send_notification_to_user(
            user=user,
            title=title,
            body=body,
            data=data,
            notification_type='document_ready',
            priority='normal'
        )


# Singleton instance
notification_service = NotificationService()
