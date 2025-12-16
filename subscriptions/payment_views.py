"""
Unified Payment API Views
Single endpoint for all payment types (subscriptions, credits, documents, materials)
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator

from .models import PaymentTransaction
from .public_serializers import PaymentTransactionSerializer
from .payment_service import payment_service, PaymentServiceError

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ViewSet):
    """
    Unified payment endpoint for all purchase types
    
    Endpoints:
    - POST /payments/initiate/ - Initiate payment
    - GET /payments/{id}/status/ - Check payment status
    - GET /payments/my-payments/ - Payment history
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate_payment(self, request):
        """
        Initiate a payment for any category
        
        POST /api/v1/subscriptions/payments/initiate/
        
        Request Body:
        {
            "payment_category": "subscription",  // or "call_credit", "document", "material"
            "item_id": 1,                        // ID of plan/bundle/document/material
            "payment_method": "mobile_money",    // or "bank"
            "phone_number": "255712345678",      // For mobile money
            "provider": "mpesa",                 // Optional: mpesa, airtel_money, tigo_pesa
            
            // Optional for bank payments
            "bank_name": "CRDB",
            "merchant_mobile": "255712345678",
            "otp": "123456"
        }
        
        Response:
        {
            "success": true,
            "transaction": {transaction_object},
            "payment": {azampay_response},
            "next_steps": [...]
        }
        """
        # Extract parameters
        payment_category = request.data.get('payment_category')
        item_id = request.data.get('item_id')
        payment_method = request.data.get('payment_method', 'mobile_money')
        phone_number = request.data.get('phone_number')
        provider = request.data.get('provider')
        
        # Validation
        if not payment_category:
            return Response({
                'error': 'payment_category is required',
                'valid_categories': ['subscription', 'call_credit', 'document', 'material']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not item_id:
            return Response({
                'error': 'item_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if payment_method == 'mobile_money' and not phone_number:
            return Response({
                'error': 'phone_number is required for mobile money payments'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initiate payment through unified service
            result = payment_service.initiate_payment(
                user=request.user,
                payment_category=payment_category,
                item_id=item_id,
                payment_method=payment_method,
                phone_number=phone_number,
                provider=provider,
                bank_name=request.data.get('bank_name'),
                merchant_mobile=request.data.get('merchant_mobile'),
                otp=request.data.get('otp')
            )
            
            # Format response
            response_data = {
                'success': result['success'],
                'message': result['message'],
                'transaction': PaymentTransactionSerializer(result['transaction']).data,
                'payment': {
                    'azampay_transaction_id': result['payment_details'].get('transaction_id'),
                    'status': result['payment_details'].get('status', 'processing'),
                    'provider_response': result['payment_details'].get('provider_response', {}),
                },
                'next_steps': self._get_next_steps(payment_method, result['transaction'])
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except PaymentServiceError as e:
            logger.error(f"Payment initiation error: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Unexpected error in payment initiation: {e}")
            return Response({
                'error': 'Payment initiation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='status')
    def check_status(self, request, pk=None):
        """
        Check payment status
        
        GET /api/v1/subscriptions/payments/{id}/status/
        
        Response:
        {
            "transaction_id": 123,
            "status": "completed",
            "payment_reference": "PAY_SUB_...",
            "amount": 3000,
            "is_fulfilled": true,
            "fulfilled_at": "2025-12-15T10:35:00Z",
            "fulfillment": {
                "type": "subscription",
                "details": {...}
            }
        }
        """
        try:
            transaction = PaymentTransaction.objects.get(id=pk, user=request.user)
        except PaymentTransaction.DoesNotExist:
            return Response({
                'error': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Build response
        response_data = {
            'transaction_id': transaction.id,
            'status': transaction.status,
            'payment_reference': transaction.payment_reference,
            'gateway_reference': transaction.gateway_reference,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'payment_method': transaction.payment_method,
            'is_fulfilled': transaction.is_fulfilled,
            'fulfilled_at': transaction.fulfilled_at,
            'created_at': transaction.created_at,
            'updated_at': transaction.updated_at,
        }
        
        # Add fulfillment details if completed
        if transaction.status == 'completed' and transaction.is_fulfilled:
            response_data['fulfillment'] = {
                'type': transaction.transaction_type,
                'details': transaction.item_metadata,
                'related_items': PaymentTransactionSerializer(transaction).data.get('related_items')
            }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'], url_path='my-payments')
    def my_payments(self, request):
        """
        Get user's payment history with filtering and pagination
        
        GET /api/v1/subscriptions/payments/my-payments/
        
        Query Parameters:
        - category: subscription, call_credit, document, material
        - status: pending, completed, failed
        - page: 1
        - page_size: 20
        
        Response:
        {
            "count": 15,
            "page": 1,
            "page_size": 20,
            "total_pages": 1,
            "payments": [...]
        }
        """
        # Get query parameters
        category = request.query_params.get('category')
        payment_status = request.query_params.get('status')
        page_num = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        # Limit page size
        page_size = min(page_size, 100)
        
        # Build query
        payments = PaymentTransaction.objects.filter(user=request.user)
        
        # Apply filters
        if category:
            payments = payments.filter(transaction_type=category)
        
        if payment_status:
            payments = payments.filter(status=payment_status)
        
        # Order by date (newest first)
        payments = payments.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(payments, page_size)
        page_obj = paginator.get_page(page_num)
        
        # Serialize
        serializer = PaymentTransactionSerializer(page_obj.object_list, many=True)
        
        return Response({
            'count': paginator.count,
            'page': page_num,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'payments': serializer.data,
            'summary': self._get_payment_summary(payments)
        })
    
    # Helper methods
    def _get_next_steps(self, payment_method, transaction):
        """Generate next steps instructions for user"""
        if payment_method == 'mobile_money':
            return [
                "Check your phone for payment prompt",
                "Enter your PIN to confirm payment",
                "Payment will be automatically verified",
                f"You will be notified once payment is complete"
            ]
        elif payment_method == 'bank':
            return [
                "Your bank payment has been initiated",
                "Complete the payment on your bank app",
                "Payment will be verified within 5 minutes"
            ]
        return ["Payment initiated successfully"]
    
    def _get_payment_summary(self, payments_queryset):
        """Generate payment summary statistics"""
        total = payments_queryset.count()
        completed = payments_queryset.filter(status='completed').count()
        pending = payments_queryset.filter(status='pending').count()
        failed = payments_queryset.filter(status='failed').count()
        
        total_amount = sum(
            float(p.amount) 
            for p in payments_queryset.filter(status='completed')
        )
        
        return {
            'total_transactions': total,
            'completed': completed,
            'pending': pending,
            'failed': failed,
            'total_amount_spent': total_amount,
            'currency': 'TZS'
        }


# Export for URL registration
__all__ = ['PaymentViewSet']
