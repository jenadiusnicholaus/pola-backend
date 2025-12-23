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
from .disbursement_pdf_generator import DisbursementPDFGenerator


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
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"get_queryset called, action={getattr(self, 'action', 'unknown')}")
        
        # Don't apply filters for detail actions (retrieve, download_pdf, download_excel_receipt)
        if self.action in ['retrieve', 'download_pdf', 'download_excel_receipt', 'process', 'retry', 'cancel', 'check_status']:
            logger.info(f"Returning unfiltered queryset for action: {self.action}")
            return queryset
        
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
        """
        Initiate a new disbursement with automatic earnings linking
        
        Returns PDF and Excel receipts in base64 format that can be downloaded by admin.
        
        Response includes:
        - disbursement details
        - earnings_summary (linked earnings counts)
        - pdf_receipt: {base64, filename, size_bytes, mimetype}
        - excel_receipt: {base64, filename, size_bytes, mimetype}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated data
        recipient = serializer.validated_data['recipient']
        disbursement_type = serializer.validated_data['disbursement_type']
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        recipient_phone = serializer.validated_data['recipient_phone']
        notes = serializer.validated_data.get('notes', '')
        
        # AUTO-GATHER UNPAID EARNINGS
        unpaid_consultant = ConsultantEarnings.objects.filter(
            consultant=recipient,
            paid_out=False
        )
        
        unpaid_uploader = UploaderEarnings.objects.filter(
            uploader=recipient,
            paid_out=False
        )
        
        # Calculate total unpaid earnings
        total_consultant = unpaid_consultant.aggregate(
            total=Sum('net_earnings')
        )['total'] or Decimal('0.00')
        
        total_uploader = unpaid_uploader.aggregate(
            total=Sum('net_earnings')
        )['total'] or Decimal('0.00')
        
        total_unpaid = total_consultant + total_uploader
        
        # Validate requested amount
        if amount > total_unpaid:
            return Response({
                'error': f'Requested amount ({amount}) exceeds total unpaid earnings ({total_unpaid})',
                'total_consultant_earnings': str(total_consultant),
                'total_uploader_earnings': str(total_uploader),
                'total_available': str(total_unpaid),
                'unpaid_consultant_count': unpaid_consultant.count(),
                'unpaid_uploader_count': unpaid_uploader.count(),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate minimum payout amount
        if amount < Decimal('1000.00'):
            return Response({
                'error': 'Minimum disbursement amount is 1,000 TZS',
                'requested_amount': str(amount),
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # AUTO-LINK EARNINGS
        # For now, require full payout (link all unpaid earnings)
        if amount == total_unpaid:
            # Full payout - link all earnings
            disbursement.consultant_earnings.set(unpaid_consultant)
            disbursement.uploader_earnings.set(unpaid_uploader)
            
            # Mark earnings as paid out
            unpaid_consultant.update(paid_out=True, payout_date=timezone.now())
            unpaid_uploader.update(paid_out=True, payout_date=timezone.now())
        else:
            # Partial payout - link proportionally
            # Calculate how much to pay from each type
            if total_consultant > 0:
                consultant_ratio = min(amount / total_consultant, Decimal('1.00'))
                consultant_amount = total_consultant * consultant_ratio
            else:
                consultant_ratio = Decimal('0.00')
                consultant_amount = Decimal('0.00')
            
            uploader_amount = amount - consultant_amount
            
            # Link and mark consultant earnings
            if consultant_amount > 0:
                consultant_earnings_to_pay = []
                running_total = Decimal('0.00')
                for earning in unpaid_consultant:
                    if running_total + earning.net_earnings <= consultant_amount:
                        consultant_earnings_to_pay.append(earning.id)
                        running_total += earning.net_earnings
                    else:
                        break
                
                earnings_to_update = ConsultantEarnings.objects.filter(id__in=consultant_earnings_to_pay)
                disbursement.consultant_earnings.set(earnings_to_update)
                earnings_to_update.update(paid_out=True, payout_date=timezone.now())
            
            # Link and mark uploader earnings
            if uploader_amount > 0:
                uploader_earnings_to_pay = []
                running_total = Decimal('0.00')
                for earning in unpaid_uploader:
                    if running_total + earning.net_earnings <= uploader_amount:
                        uploader_earnings_to_pay.append(earning.id)
                        running_total += earning.net_earnings
                    else:
                        break
                
                earnings_to_update = UploaderEarnings.objects.filter(id__in=uploader_earnings_to_pay)
                disbursement.uploader_earnings.set(earnings_to_update)
                earnings_to_update.update(paid_out=True, payout_date=timezone.now())
        
        # Generate PDF and Excel receipts
        try:
            pdf_data = DisbursementPDFGenerator.generate_pdf(disbursement)
            excel_data = DisbursementPDFGenerator.generate_excel(disbursement)
        except Exception as e:
            # If PDF generation fails, continue without it
            pdf_data = None
            excel_data = None
        
        # Return created disbursement with earnings summary and documents
        response_serializer = DisbursementDetailSerializer(disbursement)
        response_data = response_serializer.data
        response_data['earnings_summary'] = {
            'total_unpaid_before': str(total_unpaid),
            'consultant_earnings_linked': disbursement.consultant_earnings.count(),
            'uploader_earnings_linked': disbursement.uploader_earnings.count(),
            'total_linked': str(amount),
        }
        
        # Add PDF and Excel documents in base64
        if pdf_data:
            response_data['pdf_receipt'] = {
                'base64': pdf_data['pdf_base64'],
                'filename': pdf_data['filename'],
                'size_bytes': pdf_data['size_bytes'],
                'mimetype': pdf_data['mimetype']
            }
        
        if excel_data:
            response_data['excel_receipt'] = {
                'base64': excel_data['excel_base64'],
                'filename': excel_data['filename'],
                'size_bytes': excel_data['size_bytes'],
                'mimetype': excel_data['mimetype']
            }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
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
    
    @action(detail=True, methods=['get'], url_path='download-pdf', url_name='download-pdf')
    def download_pdf(self, request, pk=None):
        """Generate and download disbursement receipt as PDF"""
        return self._generate_receipt(pk, 'pdf')
    
    @action(detail=True, methods=['get'], url_path='download-excel', url_name='download-excel')
    def download_excel_receipt(self, request, pk=None):
        """Generate and download disbursement receipt as Excel"""
        return self._generate_receipt(pk, 'excel')
    
    def _generate_receipt(self, pk, format_type):
        """Internal method to generate receipts"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generating {format_type} receipt for disbursement pk={pk}")
        
        # Fetch directly from database, bypassing get_queryset filters
        try:
            disbursement = Disbursement.objects.select_related('recipient').prefetch_related(
                'consultant_earnings', 'uploader_earnings'
            ).get(pk=pk)
            logger.info(f"Found disbursement: {disbursement.id}")
        except Disbursement.DoesNotExist:
            logger.error(f"Disbursement {pk} not found in database")
            return Response(
                {'error': f'Disbursement with id {pk} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            if format_type == 'excel':
                document_data = DisbursementPDFGenerator.generate_excel(disbursement)
                base64_key = 'excel_base64'
            else:
                document_data = DisbursementPDFGenerator.generate_pdf(disbursement)
                base64_key = 'pdf_base64'
            
            return Response({
                'success': True,
                'document': {
                    'base64': document_data[base64_key],
                    'filename': document_data['filename'],
                    'size_bytes': document_data['size_bytes'],
                    'mimetype': document_data['mimetype']
                },
                'disbursement_id': disbursement.id,
                'external_reference': disbursement.external_reference,
                'format': format_type
            })
        
        except Exception as e:
            logger.exception(f"Error generating {format_type} receipt")
            return Response(
                {'error': f'Failed to generate receipt: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """
        Export disbursements to Excel with flexible filtering
        
        Query Parameters:
        - disbursement_id: Export specific disbursement by ID
        - status: Filter by status (pending, processing, completed, failed, cancelled)
        - paid_status: Filter by paid/unpaid (paid=completed, unpaid=pending,processing,failed)
        - recipient_id: Filter by recipient user ID
        - from_date: Filter from date (YYYY-MM-DD)
        - to_date: Filter to date (YYYY-MM-DD)
        - disbursement_type: Filter by type (consultant, uploader, refund, other)
        
        Examples:
        - /api/v1/admin/disbursements/export_excel/?disbursement_id=123
        - /api/v1/admin/disbursements/export_excel/?status=completed
        - /api/v1/admin/disbursements/export_excel/?paid_status=paid
        - /api/v1/admin/disbursements/export_excel/?paid_status=unpaid
        - /api/v1/admin/disbursements/export_excel/ (exports all)
        """
        # Start with base queryset
        queryset = self.get_queryset()
        
        # Filter by specific disbursement ID
        disbursement_id = request.query_params.get('disbursement_id')
        if disbursement_id:
            queryset = queryset.filter(id=disbursement_id)
            report_title = f"Disbursement Report - ID {disbursement_id}"
        else:
            # Filter by paid/unpaid status
            paid_status = request.query_params.get('paid_status')
            if paid_status == 'paid':
                queryset = queryset.filter(status='completed')
                report_title = "Paid Disbursements Report"
            elif paid_status == 'unpaid':
                queryset = queryset.filter(status__in=['pending', 'processing', 'failed'])
                report_title = "Unpaid Disbursements Report"
            else:
                # Filter by specific status if provided
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                    report_title = f"{status_filter.title()} Disbursements Report"
                else:
                    report_title = "All Disbursements Report"
        
        # Check if any results
        if not queryset.exists():
            return Response(
                {
                    'error': 'No disbursements found matching the criteria',
                    'filters_applied': {
                        'disbursement_id': disbursement_id,
                        'status': request.query_params.get('status'),
                        'paid_status': request.query_params.get('paid_status'),
                        'recipient_id': request.query_params.get('recipient_id'),
                        'from_date': request.query_params.get('from_date'),
                        'to_date': request.query_params.get('to_date'),
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Generate Excel
            excel_data = DisbursementPDFGenerator.generate_bulk_excel(
                queryset,
                title=report_title
            )
            
            return Response({
                'success': True,
                'document': {
                    'base64': excel_data['excel_base64'],
                    'filename': excel_data['filename'],
                    'size_bytes': excel_data['size_bytes'],
                    'mimetype': excel_data['mimetype']
                },
                'report_info': {
                    'title': report_title,
                    'total_disbursements': queryset.count(),
                    'total_amount': str(queryset.aggregate(Sum('amount'))['amount__sum'] or 0),
                    'filters_applied': {
                        'disbursement_id': disbursement_id,
                        'status': request.query_params.get('status'),
                        'paid_status': request.query_params.get('paid_status'),
                        'recipient_id': request.query_params.get('recipient_id'),
                        'from_date': request.query_params.get('from_date'),
                        'to_date': request.query_params.get('to_date'),
                    }
                }
            })
        
        except Exception as e:
            return Response(
                {'error': f'Failed to generate Excel report: {str(e)}'},
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
