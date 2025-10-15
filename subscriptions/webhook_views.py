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
import logging

logger = logging.getLogger(__name__)


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
        # Payment transactions
        from .models import PaymentTransaction, ConsultationBooking, CallCreditVoucher, Disbursement
        
        # Try to find payment transaction
        try:
            payment_transaction = PaymentTransaction.objects.get(
                azampay_transaction_id=transaction_id
            )
            
            # Update payment status
            if azam_status in ['success', 'completed']:
                payment_transaction.status = 'completed'
                payment_transaction.updated_at = timezone.now()
                payment_transaction.save()
                
                # Confirm related booking or voucher
                if payment_transaction.item_type == 'consultation':
                    booking = ConsultationBooking.objects.filter(
                        booking_reference=external_reference
                    ).first()
                    if booking and booking.payment_status == 'pending':
                        booking.confirm_payment()
                
                elif payment_transaction.item_type == 'call_credit':
                    voucher = CallCreditVoucher.objects.filter(
                        order_reference=external_reference
                    ).first()
                    if voucher and voucher.status == 'pending':
                        voucher.activate()
                
                logger.info(f"Payment transaction {transaction_id} marked as completed")
            
            elif azam_status == 'failed':
                payment_transaction.status = 'failed'
                payment_transaction.updated_at = timezone.now()
                payment_transaction.save()
                logger.info(f"Payment transaction {transaction_id} marked as failed")
        
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
        'service': 'POLA AzamPay Webhook',
        'timestamp': request.META.get('HTTP_DATE')
    })
