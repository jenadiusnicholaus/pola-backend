"""
Admin Analytics & Reporting Views
Comprehensive dashboard and analytics endpoints
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from datetime import timedelta
from decimal import Decimal

from .models import (
    SubscriptionPlan, UserSubscription,
    CallCreditBundle, UserCallCredit, CallSession,
    ConsultationBooking, ConsultantEarnings,
    LearningMaterial, UploaderEarnings,
    PaymentTransaction, Disbursement
)
from authentication.models import PolaUser


@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_overview(request):
    """
    Main dashboard with key metrics
    GET /admin/analytics/dashboard/
    """
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # ===== USER METRICS =====
    total_users = PolaUser.objects.count()
    new_users_30d = PolaUser.objects.filter(date_joined__gte=thirty_days_ago).count()
    active_users = PolaUser.objects.filter(is_active=True).count()
    
    users_by_type = {
        'citizen': PolaUser.objects.filter(user_role__role_name='citizen').count(),
        'advocate': PolaUser.objects.filter(user_role__role_name='advocate').count(),
        'lawyer': PolaUser.objects.filter(user_role__role_name='lawyer').count(),
        'law_student': PolaUser.objects.filter(user_role__role_name='law_student').count(),
        'law_firm': PolaUser.objects.filter(user_role__role_name='law_firm').count(),
        'paralegal': PolaUser.objects.filter(user_role__role_name='paralegal').count()
    }
    
    # ===== SUBSCRIPTION METRICS =====
    total_subscriptions = UserSubscription.objects.count()
    active_subscriptions = UserSubscription.objects.filter(
        status='active',
        end_date__gt=now
    ).count()
    
    subscription_revenue = PaymentTransaction.objects.filter(
        transaction_type='subscription',
        status='completed',
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # ===== CALL CREDIT METRICS =====
    call_credit_purchases = UserCallCredit.objects.filter(
        purchase_date__gte=thirty_days_ago
    ).count()
    
    call_credit_revenue = PaymentTransaction.objects.filter(
        transaction_type='call_credit',
        status='completed',
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_calls_30d = CallSession.objects.filter(
        start_time__gte=thirty_days_ago
    ).count()
    
    # ===== CONSULTATION METRICS =====
    total_consultations = ConsultationBooking.objects.count()
    completed_consultations = ConsultationBooking.objects.filter(
        status='completed'
    ).count()
    
    consultation_revenue = PaymentTransaction.objects.filter(
        transaction_type='physical_consultation',
        status='completed',
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # ===== DOCUMENT METRICS =====
    total_materials = LearningMaterial.objects.count()
    approved_materials = LearningMaterial.objects.filter(is_approved=True).count()
    pending_approvals = LearningMaterial.objects.filter(is_approved=False).count()
    
    document_revenue = PaymentTransaction.objects.filter(
        transaction_type='document_download',
        status='completed',
        created_at__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # ===== REVENUE METRICS =====
    total_revenue_30d = subscription_revenue + call_credit_revenue + consultation_revenue + document_revenue
    
    total_revenue_all_time = PaymentTransaction.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Revenue breakdown
    revenue_by_type = {
        'subscriptions': subscription_revenue,
        'call_credits': call_credit_revenue,
        'consultations': consultation_revenue,
        'documents': document_revenue
    }
    
    # ===== DISBURSEMENT METRICS =====
    pending_disbursements = Disbursement.objects.filter(status='pending').count()
    pending_amount = Disbursement.objects.filter(
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_disbursed = Disbursement.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # ===== GROWTH METRICS =====
    # Compare with previous 30 days
    sixty_days_ago = now - timedelta(days=60)
    
    revenue_previous_30d = PaymentTransaction.objects.filter(
        status='completed',
        created_at__gte=sixty_days_ago,
        created_at__lt=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    if revenue_previous_30d > 0:
        revenue_growth = ((total_revenue_30d - revenue_previous_30d) / revenue_previous_30d * 100)
    else:
        revenue_growth = 100 if total_revenue_30d > 0 else 0
    
    users_previous_30d = PolaUser.objects.filter(
        date_joined__gte=sixty_days_ago,
        date_joined__lt=thirty_days_ago
    ).count()
    
    if users_previous_30d > 0:
        user_growth = ((new_users_30d - users_previous_30d) / users_previous_30d * 100)
    else:
        user_growth = 100 if new_users_30d > 0 else 0
    
    return Response({
        'users': {
            'total': total_users,
            'new_30d': new_users_30d,
            'active': active_users,
            'by_type': users_by_type,
            'growth_rate': round(Decimal(user_growth), 2)
        },
        'subscriptions': {
            'total': total_subscriptions,
            'active': active_subscriptions,
            'revenue_30d': subscription_revenue
        },
        'call_credits': {
            'purchases_30d': call_credit_purchases,
            'revenue_30d': call_credit_revenue,
            'total_calls_30d': total_calls_30d
        },
        'consultations': {
            'total': total_consultations,
            'completed': completed_consultations,
            'revenue_30d': consultation_revenue
        },
        'documents': {
            'total': total_materials,
            'approved': approved_materials,
            'pending_approvals': pending_approvals,
            'revenue_30d': document_revenue
        },
        'revenue': {
            'total_30d': total_revenue_30d,
            'total_all_time': total_revenue_all_time,
            'by_type': revenue_by_type,
            'growth_rate': round(Decimal(revenue_growth), 2)
        },
        'disbursements': {
            'pending_count': pending_disbursements,
            'pending_amount': pending_amount,
            'total_disbursed': total_disbursed
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def revenue_analytics(request):
    """
    Detailed revenue analytics
    GET /admin/analytics/revenue/?period=daily
    """
    period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, yearly
    transaction_type = request.query_params.get('type')  # Filter by transaction type
    
    now = timezone.now()
    
    if period == 'weekly':
        start_date = now - timedelta(weeks=12)
    elif period == 'monthly':
        start_date = now - timedelta(days=365)
    elif period == 'yearly':
        start_date = now - timedelta(days=365 * 3)
    else:  # daily
        start_date = now - timedelta(days=30)
    
    # Get payments
    payments = PaymentTransaction.objects.filter(
        status='completed',
        created_at__gte=start_date
    ).order_by('created_at')
    
    if transaction_type:
        payments = payments.filter(transaction_type=transaction_type)
    
    # Group by period
    revenue_data = {}
    for payment in payments:
        if period == 'weekly':
            key = f"{payment.created_at.year}-W{payment.created_at.isocalendar()[1]}"
        elif period == 'monthly':
            key = payment.created_at.strftime('%Y-%m')
        elif period == 'yearly':
            key = str(payment.created_at.year)
        else:  # daily
            key = payment.created_at.strftime('%Y-%m-%d')
        
        if key not in revenue_data:
            revenue_data[key] = {
                'period': key,
                'total_revenue': Decimal('0'),
                'subscription': Decimal('0'),
                'call_credit': Decimal('0'),
                'physical_consultation': Decimal('0'),
                'document_download': Decimal('0'),
                'transaction_count': 0
            }
        
        revenue_data[key]['total_revenue'] += payment.amount
        revenue_data[key][payment.transaction_type] += payment.amount
        revenue_data[key]['transaction_count'] += 1
    
    return Response({
        'period': period,
        'transaction_type': transaction_type or 'all',
        'data': list(revenue_data.values())
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_analytics(request):
    """
    User analytics and trends
    GET /admin/analytics/users/
    """
    now = timezone.now()
    
    # User growth over last 12 months
    user_growth = []
    for i in range(12):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
        if i == 0:
            month_end = now
        else:
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1, hour=0, minute=0, second=0) - timedelta(seconds=1)
        
        month_key = month_start.strftime('%Y-%m')
        new_users = PolaUser.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        
        user_growth.insert(0, {
            'period': month_key,
            'new_users': new_users
        })
    
    # User engagement
    thirty_days_ago = now - timedelta(days=30)
    
    # Active users by type
    active_by_type = {}
    for user_type in ['client', 'consultant', 'student', 'lecturer', 'admin']:
        active_count = PolaUser.objects.filter(
            user_type=user_type,
            is_active=True
        ).count()
        
        # Has activity in last 30 days (made payment or login)
        engaged_count = PolaUser.objects.filter(
            user_type=user_type,
            is_active=True,
            last_login__gte=thirty_days_ago
        ).count()
        
        active_by_type[user_type] = {
            'total': PolaUser.objects.filter(user_type=user_type).count(),
            'active': active_count,
            'engaged_30d': engaged_count
        }
    
    # User retention
    # Users who joined 60-90 days ago and are still active
    ninety_days_ago = now - timedelta(days=90)
    sixty_days_ago = now - timedelta(days=60)
    
    cohort_users = PolaUser.objects.filter(
        date_joined__gte=ninety_days_ago,
        date_joined__lt=sixty_days_ago
    )
    cohort_count = cohort_users.count()
    
    retained_users = cohort_users.filter(
        is_active=True,
        last_login__gte=thirty_days_ago
    ).count()
    
    retention_rate = (retained_users / cohort_count * 100) if cohort_count > 0 else 0
    
    return Response({
        'user_growth': user_growth,
        'active_by_type': active_by_type,
        'retention': {
            'cohort_size': cohort_count,
            'retained': retained_users,
            'retention_rate': round(Decimal(retention_rate), 2)
        }
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def platform_health(request):
    """
    Platform health metrics
    GET /admin/analytics/health/
    """
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # Payment success rate
    all_payments_30d = PaymentTransaction.objects.filter(
        created_at__gte=thirty_days_ago
    )
    completed_payments = all_payments_30d.filter(status='completed').count()
    total_payments = all_payments_30d.count()
    payment_success_rate = (completed_payments / total_payments * 100) if total_payments > 0 else 0
    
    # Failed payments
    failed_payments = all_payments_30d.filter(status='failed').count()
    
    # Pending disbursements
    pending_disbursements = Disbursement.objects.filter(status='pending')
    pending_count = pending_disbursements.count()
    pending_amount = pending_disbursements.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Average processing time for completed disbursements (last 30 days)
    completed_disbursements = Disbursement.objects.filter(
        status='completed',
        completed_at__gte=thirty_days_ago
    )
    
    if completed_disbursements.count() > 0:
        processing_times = []
        for d in completed_disbursements:
            if d.completed_at and d.created_at:
                delta = d.completed_at - d.created_at
                processing_times.append(delta.total_seconds() / 3600)  # hours
        
        avg_processing_hours = sum(processing_times) / len(processing_times)
    else:
        avg_processing_hours = 0
    
    # Consultation metrics
    all_bookings_30d = ConsultationBooking.objects.filter(
        created_at__gte=thirty_days_ago
    )
    cancelled_rate = (
        all_bookings_30d.filter(status='cancelled').count() / all_bookings_30d.count() * 100
    ) if all_bookings_30d.count() > 0 else 0
    
    # Average rating
    avg_rating = ConsultationBooking.objects.filter(
        status='completed',
        rating__isnull=False
    ).aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Material approval backlog
    pending_approvals = LearningMaterial.objects.filter(is_approved=False).count()
    
    # Oldest pending approval
    oldest_pending = LearningMaterial.objects.filter(
        is_approved=False
    ).order_by('created_at').first()
    
    days_pending = 0
    if oldest_pending:
        days_pending = (now - oldest_pending.created_at).days
    
    return Response({
        'payments': {
            'success_rate': round(Decimal(payment_success_rate), 2),
            'failed_count': failed_payments,
            'total_count': total_payments
        },
        'disbursements': {
            'pending_count': pending_count,
            'pending_amount': pending_amount,
            'avg_processing_hours': round(Decimal(avg_processing_hours), 2)
        },
        'consultations': {
            'cancellation_rate': round(Decimal(cancelled_rate), 2),
            'average_rating': round(Decimal(avg_rating), 2)
        },
        'approvals': {
            'pending_count': pending_approvals,
            'oldest_pending_days': days_pending
        }
    })
