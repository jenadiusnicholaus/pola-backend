"""
Admin Disbursement Views - Manual Payout Management

This module provides admin APIs for managing disbursements (payouts) to consultants and uploaders.
Admins can initiate payouts through AzamPay, track disbursement status, and view earnings.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Q, Sum, Count, Case, When, DecimalField, Value
from django.utils import timezone
from decimal import Decimal

from .models import (
    Disbursement,
    ConsultantEarnings,
    UploaderEarnings,
)
from .serializers import (
    DisbursementSerializer,
    DisbursementDetailSerializer,
    InitiateDisbursementSerializer,
    ConsultantEarningsSerializer,
    UploaderEarningsSerializer,
    EarningsSummarySerializer,
)
from .azampay_integration import azampay_client, AzamPayError
from authentication.models import PolaUser


class AdminDisbursementViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing disbursements (payouts)
    
    Endpoints:
    - GET /admin/disbursements/ - List all disbursements
    - POST /admin/disbursements/ - Initiate a new disbursement
    - GET /admin/disbursements/{id}/ - Get disbursement details
    - POST /admin/disbursements/{id}/process/ - Process a pending or failed disbursement
    - POST /admin/disbursements/{id}/retry/ - Retry a failed disbursement
    - POST /admin/disbursements/{id}/cancel/ - Cancel a pending disbursement
    - POST /admin/disbursements/{id}/check_status/ - Check AzamPay status
    - GET /admin/disbursements/pending/ - List pending disbursements
    - GET /admin/disbursements/statistics/ - Get disbursement statistics
    """
    queryset = Disbursement.objects.all().select_related(
        'recipient', 'initiated_by'
    ).prefetch_related('consultant_earnings', 'uploader_earnings')
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DisbursementDetailSerializer
        elif self.action == 'create':
            return InitiateDisbursementSerializer
        return DisbursementSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        type_filter = self.request.query_params.get('type', None)
        if type_filter:
            queryset = queryset.filter(disbursement_type=type_filter)
        
        # Filter by recipient
        recipient_id = self.request.query_params.get('recipient_id', None)
        if recipient_id:
            queryset = queryset.filter(recipient_id=recipient_id)
        
        # Date range filters
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        
        if from_date:
            queryset = queryset.filter(initiated_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(initiated_at__lte=to_date)
        
        return queryset.order_by('-initiated_at')
    
    def create(self, request, *args, **kwargs):
        """Initiate a new disbursement"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated data
        recipient = serializer.validated_data['recipient']
        disbursement_type = serializer.validated_data['disbursement_type']
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        recipient_phone = serializer.validated_data['recipient_phone']
        notes = serializer.validated_data.get('notes', '')
        
        # Create disbursement record
        disbursement = Disbursement.objects.create(
            recipient=recipient,
            recipient_phone=recipient_phone,
            disbursement_type=disbursement_type,
            amount=amount,
            payment_method=payment_method,
            initiated_by=request.user,
            notes=notes,
            status='pending'
        )
        
        # Link related earnings if provided
        if 'consultant_earnings' in serializer.validated_data:
            disbursement.consultant_earnings.set(serializer.validated_data['consultant_earnings'])
        
        if 'uploader_earnings' in serializer.validated_data:
            disbursement.uploader_earnings.set(serializer.validated_data['uploader_earnings'])
        
        # Return created disbursement
        response_serializer = DisbursementDetailSerializer(disbursement)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process/initiate a pending or failed disbursement through AzamPay"""
        disbursement = self.get_object()
        
        # Allow processing of pending or failed disbursements (to enable retries)
        if disbursement.status not in ['pending', 'failed']:
            return Response(
                {'error': f'Cannot process disbursement with status: {disbursement.status}. Only pending or failed disbursements can be processed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate minimum amount
        if disbursement.amount < 1000:
            return Response(
                {'error': 'Minimum disbursement amount is 1,000 TZS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initiate disbursement through AzamPay
            result = azampay_client.process_disbursement(
                destination_account=disbursement.recipient_phone,
                amount=float(disbursement.amount),
                external_reference=disbursement.external_reference,
                recipient_name=disbursement.recipient_name,
                disbursement_type=disbursement.payment_method if disbursement.payment_method != 'bank_transfer' else 'bank_transfer',
                provider=disbursement.payment_method if disbursement.payment_method != 'bank_transfer' else None,
                remarks=f"{disbursement.disbursement_type.title()} earnings payout to {disbursement.recipient.email}"
            )
            
            if result.get('success'):
                # Update disbursement record
                disbursement.azampay_transaction_id = result.get('transaction_id')
                disbursement.status = 'processing'
                disbursement.processed_at = timezone.now()
                disbursement.save()
                
                # If mock mode and already completed, mark as completed
                if result.get('status') == 'completed' and result.get('mock_mode'):
                    disbursement.mark_completed(transaction_id=result.get('transaction_id'))
                
                return Response({
                    'message': 'Disbursement initiated successfully',
                    'disbursement_id': disbursement.id,
                    'external_reference': disbursement.external_reference,
                    'azampay_transaction_id': disbursement.azampay_transaction_id,
                    'status': disbursement.status,
                    'amount': float(disbursement.amount),
                    'recipient': disbursement.recipient.email,
                    'phone': disbursement.recipient_phone,
                    'azampay_response': result
                })
            else:
                # Mark as failed
                error_msg = result.get('message', 'Disbursement failed')
                disbursement.mark_failed(error_msg)
                
                return Response(
                    {
                        'error': error_msg,
                        'azampay_response': result
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except AzamPayError as e:
            # Mark as failed
            disbursement.mark_failed(str(e))
            
            return Response(
                {'error': f'AzamPay error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            # Mark as failed
            disbursement.mark_failed(f'Unexpected error: {str(e)}')
            
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed disbursement - convenience endpoint that calls process"""
        disbursement = self.get_object()
        
        if disbursement.status != 'failed':
            return Response(
                {'error': f'Can only retry failed disbursements. Current status: {disbursement.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add retry note
        disbursement.notes += f"\n[Retry initiated by {request.user.email} at {timezone.now().isoformat()}]"
        disbursement.save()
        
        # Call the process method to retry
        return self.process(request, pk)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending disbursement"""
        disbursement = self.get_object()
        
        if disbursement.status != 'pending':
            return Response(
                {'error': f'Cannot cancel disbursement with status: {disbursement.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        disbursement.status = 'cancelled'
        disbursement.notes += f"\n[Cancelled by {request.user.email} at {timezone.now().isoformat()}]"
        disbursement.save()
        
        serializer = DisbursementSerializer(disbursement)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def check_status(self, request, pk=None):
        """Check disbursement status from AzamPay"""
        disbursement = self.get_object()
        
        if not disbursement.azampay_transaction_id:
            return Response(
                {'error': 'No AzamPay transaction ID found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check status from AzamPay
            result = azampay_client.check_disbursement_status(
                transaction_id=disbursement.azampay_transaction_id
            )
            
            # Update status if changed
            azam_status = result.get('status', '').lower()
            if azam_status == 'success' or azam_status == 'completed':
                if disbursement.status != 'completed':
                    disbursement.mark_completed()
            elif azam_status == 'failed':
                if disbursement.status != 'failed':
                    disbursement.mark_failed(result.get('message', 'Payment failed'))
            
            serializer = DisbursementSerializer(disbursement)
            return Response({
                'disbursement': serializer.data,
                'azampay_status': result
            })
        
        except AzamPayError as e:
            return Response(
                {'error': f'AzamPay error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending disbursements"""
        pending_disbursements = self.get_queryset().filter(status='pending')
        
        serializer = self.get_serializer(pending_disbursements, many=True)
        return Response({
            'count': pending_disbursements.count(),
            'total_amount': pending_disbursements.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0'),
            'disbursements': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get disbursement statistics"""
        queryset = self.get_queryset()
        
        # Overall stats
        total_count = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Status breakdown
        status_stats = {}
        for status_choice, _ in Disbursement.DISBURSEMENT_STATUS:
            status_queryset = queryset.filter(status=status_choice)
            status_stats[status_choice] = {
                'count': status_queryset.count(),
                'total_amount': float(status_queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0'))
            }
        
        # Type breakdown
        type_stats = {}
        for type_choice, _ in Disbursement.DISBURSEMENT_TYPE:
            type_queryset = queryset.filter(disbursement_type=type_choice)
            type_stats[type_choice] = {
                'count': type_queryset.count(),
                'total_amount': float(type_queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0'))
            }
        
        # Payment method breakdown
        method_stats = {}
        for method_choice, _ in Disbursement.PAYMENT_METHOD:
            method_queryset = queryset.filter(payment_method=method_choice)
            method_stats[method_choice] = {
                'count': method_queryset.count(),
                'total_amount': float(method_queryset.aggregate(total=Sum('amount'))['total'] or Decimal('0'))
            }
        
        # Recent activity
        recent_disbursements = queryset.order_by('-initiated_at')[:10]
        recent_serializer = DisbursementSerializer(recent_disbursements, many=True)
        
        return Response({
            'summary': {
                'total_count': total_count,
                'total_amount': float(total_amount),
            },
            'by_status': status_stats,
            'by_type': type_stats,
            'by_payment_method': method_stats,
            'recent_disbursements': recent_serializer.data
        })


class AdminEarningsManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ViewSet for viewing and managing earnings
    
    Endpoints:
    - GET /admin/earnings/consultant/ - List consultant earnings
    - GET /admin/earnings/uploader/ - List uploader earnings
    - GET /admin/earnings/unpaid/ - List unpaid earnings
    - GET /admin/earnings/summary/ - Get earnings summary by user
    - POST /admin/earnings/bulk_payout/ - Create bulk disbursement
    """
    permission_classes = [IsAdminUser]
    queryset = ConsultantEarnings.objects.none()  # Placeholder for schema
    serializer_class = ConsultantEarningsSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ConsultantEarnings.objects.none()
        return ConsultantEarnings.objects.none()  # Override in actions
    
    @action(detail=False, methods=['get'])
    def consultant(self, request):
        """List consultant earnings"""
        queryset = ConsultantEarnings.objects.all().select_related(
            'consultant', 'booking'
        ).order_by('-created_at')
        
        # Filter by paid status
        paid_filter = request.query_params.get('paid', None)
        if paid_filter is not None:
            queryset = queryset.filter(paid_out=(paid_filter.lower() == 'true'))
        
        # Filter by consultant
        consultant_id = request.query_params.get('consultant_id', None)
        if consultant_id:
            queryset = queryset.filter(consultant_id=consultant_id)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ConsultantEarningsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ConsultantEarningsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def uploader(self, request):
        """List uploader earnings"""
        queryset = UploaderEarnings.objects.all().select_related(
            'uploader', 'material'
        ).order_by('-created_at')
        
        # Filter by paid status
        paid_filter = request.query_params.get('paid', None)
        if paid_filter is not None:
            queryset = queryset.filter(paid_out=(paid_filter.lower() == 'true'))
        
        # Filter by uploader
        uploader_id = request.query_params.get('uploader_id', None)
        if uploader_id:
            queryset = queryset.filter(uploader_id=uploader_id)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UploaderEarningsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UploaderEarningsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unpaid(self, request):
        """List all unpaid earnings"""
        consultant_earnings = ConsultantEarnings.objects.filter(
            paid_out=False
        ).select_related('consultant', 'booking')
        
        uploader_earnings = UploaderEarnings.objects.filter(
            paid_out=False
        ).select_related('uploader', 'material')
        
        consultant_serializer = ConsultantEarningsSerializer(consultant_earnings, many=True)
        uploader_serializer = UploaderEarningsSerializer(uploader_earnings, many=True)
        
        total_consultant = consultant_earnings.aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
        total_uploader = uploader_earnings.aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
        
        return Response({
            'consultant_earnings': {
                'count': consultant_earnings.count(),
                'total_amount': float(total_consultant),
                'earnings': consultant_serializer.data
            },
            'uploader_earnings': {
                'count': uploader_earnings.count(),
                'total_amount': float(total_uploader),
                'earnings': uploader_serializer.data
            },
            'total_unpaid': float(total_consultant + total_uploader)
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get earnings summary by user"""
        user_id = request.query_params.get('user_id', None)
        
        if user_id:
            # Single user summary
            try:
                user = PolaUser.objects.get(id=user_id)
            except PolaUser.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            users = [user]
        else:
            # All users with earnings
            consultant_users = ConsultantEarnings.objects.values_list('consultant_id', flat=True).distinct()
            uploader_users = UploaderEarnings.objects.values_list('uploader_id', flat=True).distinct()
            user_ids = set(list(consultant_users) + list(uploader_users))
            users = PolaUser.objects.filter(id__in=user_ids)
        
        # Build summary for each user
        summaries = []
        for user in users:
            consultant_earnings = ConsultantEarnings.objects.filter(consultant=user)
            uploader_earnings = UploaderEarnings.objects.filter(uploader=user)
            
            consultant_total = consultant_earnings.aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
            consultant_paid = consultant_earnings.filter(paid_out=True).aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
            consultant_unpaid = consultant_total - consultant_paid
            
            uploader_total = uploader_earnings.aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
            uploader_paid = uploader_earnings.filter(paid_out=True).aggregate(total=Sum('net_earnings'))['total'] or Decimal('0')
            uploader_unpaid = uploader_total - uploader_paid
            
            summary = {
                'user_id': user.id,
                'user_email': user.email,
                'user_name': getattr(user, 'full_name', user.email),
                'total_consultant_earnings': float(consultant_total),
                'paid_consultant_earnings': float(consultant_paid),
                'unpaid_consultant_earnings': float(consultant_unpaid),
                'consultant_earnings_count': consultant_earnings.count(),
                'total_uploader_earnings': float(uploader_total),
                'paid_uploader_earnings': float(uploader_paid),
                'unpaid_uploader_earnings': float(uploader_unpaid),
                'uploader_earnings_count': uploader_earnings.count(),
                'total_earnings': float(consultant_total + uploader_total),
                'total_paid': float(consultant_paid + uploader_paid),
                'total_unpaid': float(consultant_unpaid + uploader_unpaid),
            }
            summaries.append(summary)
        
        # Sort by total unpaid descending
        summaries.sort(key=lambda x: x['total_unpaid'], reverse=True)
        
        return Response({
            'count': len(summaries),
            'summaries': summaries
        })
    
    @action(detail=False, methods=['post'])
    def bulk_payout(self, request):
        """Create bulk disbursement for unpaid earnings"""
        user_id = request.data.get('user_id')
        payment_method = request.data.get('payment_method', 'tigo_pesa')
        phone_number = request.data.get('phone_number')
        earnings_type = request.data.get('earnings_type', 'consultant')  # 'consultant', 'uploader', or 'both'
        
        if not all([user_id, phone_number]):
            return Response(
                {'error': 'user_id and phone_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = PolaUser.objects.get(id=user_id)
        except PolaUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get unpaid earnings
        consultant_earnings = []
        uploader_earnings = []
        total_amount = Decimal('0')
        
        if earnings_type in ['consultant', 'both']:
            consultant_earnings = list(ConsultantEarnings.objects.filter(
                consultant=user,
                paid_out=False
            ))
            total_amount += sum([e.net_earnings for e in consultant_earnings], Decimal('0'))
        
        if earnings_type in ['uploader', 'both']:
            uploader_earnings = list(UploaderEarnings.objects.filter(
                uploader=user,
                paid_out=False
            ))
            total_amount += sum([e.net_earnings for e in uploader_earnings], Decimal('0'))
        
        if total_amount == 0:
            return Response(
                {'error': 'No unpaid earnings found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create disbursement
        disbursement = Disbursement.objects.create(
            recipient=user,
            recipient_phone=phone_number,
            disbursement_type=earnings_type if earnings_type != 'both' else 'consultant',
            amount=total_amount,
            payment_method=payment_method,
            initiated_by=request.user,
            notes=f"Bulk payout for {earnings_type} earnings",
            status='pending'
        )
        
        # Link earnings
        if consultant_earnings:
            disbursement.consultant_earnings.set(consultant_earnings)
        if uploader_earnings:
            disbursement.uploader_earnings.set(uploader_earnings)
        
        serializer = DisbursementDetailSerializer(disbursement)
        return Response({
            'message': f'Bulk disbursement created for {user.email}',
            'disbursement': serializer.data,
            'consultant_earnings_count': len(consultant_earnings),
            'uploader_earnings_count': len(uploader_earnings),
            'total_amount': float(total_amount)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def verify_account(self, request):
        """
        Verify account name before creating disbursement (Name Inquiry)
        
        Body:
        {
            "account_number": "255712345678",
            "bank_code": "NMB" (optional, for bank accounts)
        }
        """
        account_number = request.data.get('account_number')
        bank_code = request.data.get('bank_code')
        
        if not account_number:
            return Response(
                {'error': 'account_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = azampay_client.disbursement.name_inquiry(
                account_number=account_number,
                bank_code=bank_code
            )
            
            return Response({
                'success': True,
                'account_number': account_number,
                'account_name': result.get('account_name'),
                'bank_name': result.get('bank_name'),
                'message': result.get('message'),
                'verified': True
            })
            
        except AzamPayError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': 'Account verification failed'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
