"""
AzamPay Webhook Views

Handles payment callbacks from AzamPay gateway
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from notification.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)


def _send_payment_notification(payment_transaction):
    """Send notification when payment is received"""
    try:
        # Determine who should receive the notification based on payment type
        if payment_transaction.transaction_type == 'consultation':
            # Find the booking and notify the consultant
            from .models import ConsultationBooking
            try:
                booking = ConsultationBooking.objects.get(
                    id=payment_transaction.related_consultation_id
                )
                notification_service.send_payment_received_notification(
                    recipient=booking.consultant,
                    payer=payment_transaction.user,
                    amount=str(payment_transaction.amount),
                    currency=payment_transaction.currency,
                    payment_id=payment_transaction.id,
                    service_type='consultation'
                )
            except ConsultationBooking.DoesNotExist:
                logger.warning(f"Consultation booking not found for payment {payment_transaction.id}")
        
        elif payment_transaction.transaction_type == 'document':
            # Document purchase - notify document creator/owner if applicable
            # For now, just log it
            logger.info(f"Document purchase payment received: {payment_transaction.id}")
        
        elif payment_transaction.transaction_type == 'subscription':
            # Subscription payment - internal, no notification needed
            logger.info(f"Subscription payment received: {payment_transaction.id}")
        
    except Exception as e:
        logger.error(f"Failed to send payment notification: {str(e)}")


@api_view(['POST'])
@permission_classes([AllowAny])  # Webhook doesn't use standard auth
@csrf_exempt
def azampay_webhook(request):
    """
    AzamPay payment callback webhook
    
    This endpoint receives payment status updates from AzamPay
    URL: /api/v1/subscriptions/webhooks/azampay/
    """
    try:
        payload = request.data
        signature = request.headers.get('X-Signature', '')
        
        logger.info(f"Received AzamPay webhook: {payload}")
        
        # Extract transaction details
        transaction_id = payload.get('transactionId') or payload.get('transaction_id')
        azam_status = payload.get('status', '').lower()
        external_reference = payload.get('externalId') or payload.get('external_reference')
        
        if not transaction_id:
            logger.warning("No transaction ID in webhook payload")
            return Response({
                'success': False,
                'message': 'Missing transaction ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process based on transaction type (payment or disbursement)
        from .models import PaymentTransaction, Disbursement
        from .payment_service import payment_service, PaymentServiceError
        
        # Try to find payment transaction by gateway_reference or payment_reference
        try:
            # First try by gateway reference (AzamPay transaction ID)
            try:
                payment_transaction = PaymentTransaction.objects.get(
                    gateway_reference=transaction_id
                )
            except PaymentTransaction.DoesNotExist:
                # Try by payment reference (external_reference)
                payment_transaction = PaymentTransaction.objects.get(
                    payment_reference=external_reference
                )
            
            # Update payment status based on AzamPay response
            if azam_status in ['success', 'completed', 'successful']:
                payment_transaction.status = 'completed'
                payment_transaction.updated_at = timezone.now()
                payment_transaction.save()
                
                logger.info(f"✅ Payment {external_reference} marked as completed")
                
                # NEW: Use payment service to fulfill the purchase
                try:
                    payment_service.fulfill_payment(payment_transaction)
                    logger.info(f"✅ Payment {external_reference} fulfilled successfully")
                    
                    # Send payment received notification to the recipient
                    _send_payment_notification(payment_transaction)
                    
                except PaymentServiceError as e:
                    logger.error(f"❌ Fulfillment error for {external_reference}: {e}")
                    # Don't fail the webhook, but log the error
                    payment_transaction.fulfillment_notes = f"Fulfillment error: {str(e)}"
                    payment_transaction.save()
            
            elif azam_status in ['failed', 'failure', 'rejected', 'declined']:
                payment_transaction.status = 'failed'
                payment_transaction.updated_at = timezone.now()
                payment_transaction.fulfillment_notes = payload.get('message', 'Payment failed')
                payment_transaction.save()
                logger.info(f"❌ Payment {external_reference} marked as failed")
        
        except PaymentTransaction.DoesNotExist:
            # Try to find disbursement by transaction ID or external reference
            try:
                disbursement = Disbursement.objects.get(
                    azampay_transaction_id=transaction_id
                )
            except Disbursement.DoesNotExist:
                # Try finding by external reference
                try:
                    disbursement = Disbursement.objects.get(
                        external_reference=external_reference
                    )
                    # Update the AzamPay transaction ID if it wasn't set
                    if not disbursement.azampay_transaction_id:
                        disbursement.azampay_transaction_id = transaction_id
                        disbursement.save()
                except Disbursement.DoesNotExist:
                    logger.warning(f"Transaction {transaction_id} / {external_reference} not found in database")
                    disbursement = None
            
            if disbursement:
                # Update disbursement status based on AzamPay response
                if azam_status in ['success', 'successful', 'completed', 'success']:
                    if disbursement.status != 'completed':
                        disbursement.mark_completed(transaction_id=transaction_id)
                        logger.info(f"Disbursement {transaction_id} marked as completed via webhook")
                
                elif azam_status in ['failed', 'failure', 'rejected', 'declined']:
                    if disbursement.status != 'failed':
                        failure_reason = payload.get('message') or payload.get('reason') or 'Disbursement failed'
                        disbursement.mark_failed(failure_reason)
                        logger.info(f"Disbursement {transaction_id} marked as failed: {failure_reason}")
                
                elif azam_status in ['pending', 'processing', 'initiated']:
                    if disbursement.status == 'pending':
                        disbursement.status = 'processing'
                        disbursement.save()
                        logger.info(f"Disbursement {transaction_id} status updated to processing")
                
                else:
                    logger.warning(f"Unknown disbursement status '{azam_status}' for transaction {transaction_id}")
        
        return Response({
            'success': True,
            'message': 'Webhook processed successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_health(request):
    """
    Webhook health check endpoint
    Used by AzamPay to verify webhook is accessible
    """
    return Response({
        'status': 'healthy',
        'message': 'Webhook endpoint is accessible'
    })


@api_view(['POST'])
@permission_classes([AllowAny])  # For testing only
def manual_fulfill_payment(request):
    """
    TESTING ONLY: Manually trigger payment fulfillment
    
    Use this if webhook didn't arrive or failed
    POST body: {"payment_reference": "PAY-1234567890-123"}
    """
    from .models import PaymentTransaction
    from .payment_service import payment_service, PaymentServiceError
    
    payment_reference = request.data.get('payment_reference')
    
    if not payment_reference:
        return Response({
            'success': False,
            'message': 'payment_reference is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        payment_txn = PaymentTransaction.objects.get(payment_reference=payment_reference)
        
        logger.info(f"🔧 Manual fulfillment requested for: {payment_reference}")
        logger.info(f"   Status: {payment_txn.status}")
        logger.info(f"   Type: {payment_txn.transaction_type}")
        logger.info(f"   Amount: {payment_txn.amount} {payment_txn.currency}")
        logger.info(f"   User: {payment_txn.user.email}")
        logger.info(f"   Is Fulfilled: {payment_txn.is_fulfilled}")
        
        if payment_txn.is_fulfilled:
            return Response({
                'success': False,
                'message': 'Payment already fulfilled',
                'payment': {
                    'reference': payment_txn.payment_reference,
                    'status': payment_txn.status,
                    'type': payment_txn.transaction_type,
                    'fulfilled_at': payment_txn.fulfilled_at
                }
            })
        
        if payment_txn.status != 'completed':
            # Force complete it for testing
            logger.warning(f"⚠️ Forcing status to completed for testing: {payment_reference}")
            payment_txn.status = 'completed'
            payment_txn.save()
        
        # Try to fulfill
        try:
            payment_service.fulfill_payment(payment_txn)
            
            return Response({
                'success': True,
                'message': 'Payment fulfilled successfully',
                'payment': {
                    'reference': payment_txn.payment_reference,
                    'status': payment_txn.status,
                    'type': payment_txn.transaction_type,
                    'fulfilled': payment_txn.is_fulfilled,
                    'fulfilled_at': payment_txn.fulfilled_at
                }
            })
        except PaymentServiceError as e:
            logger.error(f"❌ Fulfillment failed: {str(e)}")
            return Response({
                'success': False,
                'message': f'Fulfillment failed: {str(e)}',
                'payment': {
                    'reference': payment_txn.payment_reference,
                    'status': payment_txn.status,
                    'type': payment_txn.transaction_type,
                    'error': str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except PaymentTransaction.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Payment not found: {payment_reference}'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in manual fulfillment: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'\
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({
        'status': 'healthy',
        'service': 'POLA AzamPay Webhook',
        'timestamp': request.META.get('HTTP_DATE')
    })
