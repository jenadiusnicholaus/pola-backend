"""
Admin Document Management Views
Handles learning materials approval, pricing, and analytics
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from decimal import Decimal

from .models import LearningMaterial, PaymentTransaction, UploaderEarnings
from .admin_document_serializers import (
    LearningMaterialAdminSerializer,
    ApproveMaterialSerializer,
    UpdateMaterialPriceSerializer,
    DocumentStatsSerializer
)
from authentication.models import PolaUser


class LearningMaterialViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing learning materials
    
    Endpoints:
    - GET    /admin/documents/materials/          - List all materials
    - POST   /admin/documents/materials/          - Create material
    - GET    /admin/documents/materials/{id}/     - Get material details
    - PUT    /admin/documents/materials/{id}/     - Update material
    - DELETE /admin/documents/materials/{id}/     - Delete material
    - POST   /admin/documents/materials/{id}/approve/      - Approve material
    - POST   /admin/documents/materials/{id}/update-price/ - Update price
    - POST   /admin/documents/materials/{id}/toggle-active/ - Toggle active
    - GET    /admin/documents/pending/            - Get pending approvals
    - GET    /admin/documents/stats/              - Statistics
    - GET    /admin/documents/revenue/            - Revenue reports
    """
    queryset = LearningMaterial.objects.all()
    serializer_class = LearningMaterialAdminSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = super().get_queryset()
        
        # Filter by approval status
        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by material type
        material_type = self.request.query_params.get('material_type')
        if material_type:
            queryset = queryset.filter(material_type=material_type)
        
        # Filter by uploader
        uploader_id = self.request.query_params.get('uploader_id')
        if uploader_id:
            queryset = queryset.filter(uploader_id=uploader_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve or reject a material"""
        material = self.get_object()
        serializer = ApproveMaterialSerializer(data=request.data)
        
        if serializer.is_valid():
            is_approved = serializer.validated_data['is_approved']
            admin_note = serializer.validated_data.get('admin_note', '')
            
            material.is_approved = is_approved
            material.save()
            
            return Response({
                'success': True,
                'message': f"Material {'approved' if is_approved else 'rejected'}",
                'admin_note': admin_note,
                'material': LearningMaterialAdminSerializer(material).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_price(self, request, pk=None):
        """Update material price"""
        material = self.get_object()
        serializer = UpdateMaterialPriceSerializer(data=request.data)
        
        if serializer.is_valid():
            new_price = serializer.validated_data['price']
            reason = serializer.validated_data.get('reason', '')
            old_price = material.price
            
            material.price = new_price
            material.save()
            
            return Response({
                'success': True,
                'message': f"Price updated from {old_price} to {new_price}",
                'reason': reason,
                'material': LearningMaterialAdminSerializer(material).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle material active status"""
        material = self.get_object()
        is_active = request.data.get('is_active', not material.is_active)
        
        material.is_active = is_active
        material.save()
        
        return Response({
            'success': True,
            'message': f"Material {'activated' if is_active else 'deactivated'}",
            'material': LearningMaterialAdminSerializer(material).data
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending approval materials"""
        pending_materials = LearningMaterial.objects.filter(
            is_approved=False
        ).order_by('-created_at')
        
        serializer = LearningMaterialAdminSerializer(pending_materials, many=True)
        
        return Response({
            'count': pending_materials.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get document statistics"""
        # Materials
        all_materials = LearningMaterial.objects.all()
        total_materials = all_materials.count()
        approved_materials = all_materials.filter(is_approved=True).count()
        pending_materials = all_materials.filter(is_approved=False).count()
        active_materials = all_materials.filter(is_active=True).count()
        
        # By type
        student_materials = all_materials.filter(
            uploader__user_type='student'
        ).count()
        lecturer_materials = all_materials.filter(
            uploader__user_type='lecturer'
        ).count()
        admin_materials = all_materials.filter(
            uploader__user_type='admin'
        ).count()
        
        # Downloads
        all_payments = PaymentTransaction.objects.filter(
            transaction_type='document_download'
        )
        total_downloads = all_materials.aggregate(
            total=Sum('download_count')
        )['total'] or 0
        paid_downloads = all_payments.filter(status='completed').count()
        
        # Revenue
        total_revenue = all_payments.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        total_uploader_earnings = UploaderEarnings.objects.all().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        total_platform_earnings = total_revenue - total_uploader_earnings
        
        # Uploaders
        total_uploaders = all_materials.values('uploader').distinct().count()
        
        # Active uploaders (uploaded in last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_uploaders = all_materials.filter(
            created_at__gte=thirty_days_ago
        ).values('uploader').distinct().count()
        
        stats = {
            'total_materials': total_materials,
            'approved_materials': approved_materials,
            'pending_materials': pending_materials,
            'active_materials': active_materials,
            'student_materials': student_materials,
            'lecturer_materials': lecturer_materials,
            'admin_materials': admin_materials,
            'total_downloads': total_downloads,
            'paid_downloads': paid_downloads,
            'total_revenue': total_revenue,
            'total_platform_earnings': total_platform_earnings,
            'total_uploader_earnings': total_uploader_earnings,
            'total_uploaders': total_uploaders,
            'active_uploaders': active_uploaders
        }
        
        serializer = DocumentStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue reports over time"""
        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, yearly
        
        now = timezone.now()
        
        if period == 'weekly':
            start_date = now - timedelta(weeks=12)
        elif period == 'monthly':
            start_date = now - timedelta(days=365)
        elif period == 'yearly':
            start_date = now - timedelta(days=365 * 3)
        else:  # daily
            start_date = now - timedelta(days=30)
        
        # Get all payments in period
        payments = PaymentTransaction.objects.filter(
            transaction_type='document_download',
            status='completed',
            timestamp__gte=start_date
        ).order_by('timestamp')
        
        # Group by period
        revenue_data = {}
        for payment in payments:
            if period == 'weekly':
                key = f"{payment.timestamp.year}-W{payment.timestamp.isocalendar()[1]}"
            elif period == 'monthly':
                key = payment.timestamp.strftime('%Y-%m')
            elif period == 'yearly':
                key = str(payment.timestamp.year)
            else:  # daily
                key = payment.timestamp.strftime('%Y-%m-%d')
            
            if key not in revenue_data:
                revenue_data[key] = {
                    'period': key,
                    'total_revenue': Decimal('0'),
                    'platform_earnings': Decimal('0'),
                    'uploader_earnings': Decimal('0'),
                    'total_downloads': 0
                }
            
            # Calculate earnings based on uploader type
            material = payment.related_material
            if material:
                if material.uploader.user_type == 'student':
                    # 50/50 split
                    platform_share = payment.amount * Decimal('0.50')
                    uploader_share = payment.amount * Decimal('0.50')
                elif material.uploader.user_type == 'lecturer':
                    # 40/60 split (platform/uploader)
                    platform_share = payment.amount * Decimal('0.40')
                    uploader_share = payment.amount * Decimal('0.60')
                else:  # admin
                    # 100/0 split
                    platform_share = payment.amount
                    uploader_share = Decimal('0')
            else:
                platform_share = payment.amount
                uploader_share = Decimal('0')
            
            revenue_data[key]['total_revenue'] += payment.amount
            revenue_data[key]['platform_earnings'] += platform_share
            revenue_data[key]['uploader_earnings'] += uploader_share
            revenue_data[key]['total_downloads'] += 1
        
        return Response({
            'period': period,
            'data': list(revenue_data.values())
        })
    
    @action(detail=True, methods=['get'])
    def downloads(self, request, pk=None):
        """Get download history for a material"""
        material = self.get_object()
        
        payments = PaymentTransaction.objects.filter(
            transaction_type='document_download',
            related_material=material,
            status='completed'
        ).order_by('-timestamp')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        download_list = []
        for payment in payments[start:end]:
            download_list.append({
                'id': payment.id,
                'user_id': payment.user.id,
                'user_email': payment.user.email,
                'amount': payment.amount,
                'timestamp': payment.timestamp,
                'payment_method': payment.payment_method
            })
        
        return Response({
            'material_id': material.id,
            'material_title': material.title,
            'count': payments.count(),
            'page': page,
            'page_size': page_size,
            'results': download_list
        })
