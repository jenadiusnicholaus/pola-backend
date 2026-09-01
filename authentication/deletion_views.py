import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.shortcuts import render

from .models import AccountDeletionRequest
from .deletion_serializers import (
    AccountDeletionRequestSerializer,
    CreateAccountDeletionSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RequestAccountDeletionView(APIView):
    """
    Request account deletion or specific data deletion.
    
    For account deletion:
    - Sets user.is_active = False immediately
    - Schedules permanent deletion after 30 days (grace period)
    - User can cancel within the grace period
    
    For data deletion:
    - Deletes only the specified data categories
    - Account remains active
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateAccountDeletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        deletion_type = data['deletion_type']

        # Check for existing pending request
        existing = AccountDeletionRequest.objects.filter(
            user=request.user, status__in=['pending', 'processing']
        ).first()
        if existing:
            return Response({
                'error': 'You already have a pending deletion request.',
                'request_id': existing.id,
                'status': existing.status,
                'scheduled_deletion_date': existing.scheduled_deletion_date
            }, status=status.HTTP_400_BAD_REQUEST)

        scheduled_date = None
        if deletion_type == 'account':
            # 30-day grace period
            scheduled_date = timezone.now() + timedelta(days=30)
            # Deactivate account immediately
            request.user.is_active = False
            request.user.save(update_fields=['is_active'])
            logger.info(f"User {request.user.email} requested account deletion. Scheduled for {scheduled_date}")

        deletion_request = AccountDeletionRequest.objects.create(
            user=request.user,
            deletion_type=deletion_type,
            data_categories=data.get('data_categories', []),
            reason=data.get('reason', ''),
            scheduled_deletion_date=scheduled_date,
        )

        resp_data = {
            'message': 'Deletion request submitted successfully.',
            'request_id': deletion_request.id,
            'deletion_type': deletion_type,
            'status': deletion_request.status,
            'scheduled_deletion_date': deletion_request.scheduled_deletion_date,
        }
        if deletion_type == 'account':
            resp_data['grace_period_days'] = 30
            resp_data['note'] = (
                'Your account has been deactivated. You can cancel this request '
                'within 30 days by logging back in and calling the cancel endpoint. '
                'After 30 days, your account and all associated data will be permanently deleted.'
            )

        return Response(resp_data, status=status.HTTP_201_CREATED)


class CancelDeletionRequestView(APIView):
    """Cancel a pending account deletion request (within grace period)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        try:
            deletion_request = AccountDeletionRequest.objects.get(
                id=request_id, user=request.user, status__in=['pending', 'processing']
            )
        except AccountDeletionRequest.DoesNotExist:
            return Response(
                {'error': 'Deletion request not found or already processed.'},
                status=status.HTTP_404_NOT_FOUND
            )

        deletion_request.status = 'cancelled'
        deletion_request.save(update_fields=['status', 'updated_at'])

        # Reactivate account if it was an account deletion
        if deletion_request.deletion_type == 'account':
            request.user.is_active = True
            request.user.save(update_fields=['is_active'])

        return Response({
            'message': 'Deletion request cancelled successfully. Your account is reactivated.',
            'request_id': deletion_request.id,
            'status': 'cancelled'
        }, status=status.HTTP_200_OK)


class MyDeletionRequestsView(generics.ListAPIView):
    """List the current user's deletion requests."""
    serializer_class = AccountDeletionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AccountDeletionRequest.objects.filter(user=self.request.user)


class DeletionRequestDetailView(generics.RetrieveAPIView):
    """Get details of a specific deletion request."""
    serializer_class = AccountDeletionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AccountDeletionRequest.objects.filter(user=self.request.user)


class DeleteSpecificDataView(APIView):
    """
    Delete specific data categories without deleting the account.
    This gives users control over individual data types.
    """
    permission_classes = [permissions.IsAuthenticated]

    DATA_HANDLERS = {
        'location': 'delete_location_data',
        'device_info': 'delete_device_data',
        'call_history': 'delete_call_history',
        'documents': 'delete_documents',
        'profile': 'delete_profile_data',
    }

    def post(self, request):
        categories = request.data.get('data_categories', [])
        if not categories:
            return Response(
                {'error': 'Specify data_categories to delete.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_categories = [c for c in categories if c in self.DATA_HANDLERS or c == 'all']
        if not valid_categories:
            return Response(
                {'error': f'Invalid categories. Valid options: {list(self.DATA_HANDLERS.keys())}, "all"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = {}
        if 'all' in valid_categories:
            valid_categories = list(self.DATA_HANDLERS.keys())

        for category in valid_categories:
            handler_name = self.DATA_HANDLERS.get(category)
            if handler_name:
                handler = getattr(self, handler_name, None)
                if handler:
                    results[category] = handler(request.user)

        # Log the deletion request
        AccountDeletionRequest.objects.create(
            user=request.user,
            deletion_type='data',
            data_categories=valid_categories,
            status='completed',
            processed_at=timezone.now(),
        )

        return Response({
            'message': 'Data deletion completed.',
            'deleted': results
        }, status=status.HTTP_200_OK)

    def delete_location_data(self, user):
        from .device_models import UserDevice
        count = UserDevice.objects.filter(user=user).update(
            latitude=None, longitude=None
        )
        return f'Cleared location data from {count} device(s)'

    def delete_device_data(self, user):
        from .device_models import UserDevice
        count, _ = UserDevice.objects.filter(user=user).delete()
        return f'Deleted {count} device record(s)'

    def delete_call_history(self, user):
        try:
            from subscriptions.models import CallSession
            count, _ = CallSession.objects.filter(
                Q(caller=user) | Q(consultant=user)
            ).delete()
            return f'Deleted {count} call record(s)'
        except Exception:
            return 'Call history deletion not available'

    def delete_documents(self, user):
        try:
            from .models import Document
            count, _ = Document.objects.filter(user=user).delete()
            return f'Deleted {count} document(s)'
        except Exception:
            return 'Document deletion not available'

    def delete_profile_data(self, user):
        cleared = []
        if hasattr(user, 'contact'):
            user.contact.delete()
            cleared.append('contact')
        if hasattr(user, 'address'):
            user.address.delete()
            cleared.append('address')
        user.profile_picture = None
        user.bio = ''
        user.save()
        cleared.append('profile_picture')
        return f'Cleared: {", ".join(cleared)}'


# --- Public web pages for Play Store listing ---

def deletion_info_page(request):
    """
    Public HTML page for account deletion.
    URL for Google Play Store: /api/v1/authentication/deletion/account/
    """
    return render(request, 'account_deletion_page.html')


def data_deletion_info_page(request):
    """
    Public HTML page for data deletion (without deleting account).
    URL for Google Play Store: /api/v1/authentication/deletion/data/
    """
    return render(request, 'data_deletion_page.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def public_deletion_request(request):
    """
    Public endpoint (no auth required) to submit an account deletion request
    by providing email. Used by the public web page.
    """
    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()
    if not user:
        # Don't reveal whether email exists
        return Response({
            'message': 'If an account exists for this email, a deletion request has been submitted. '
                       'You will receive a confirmation email with further instructions.'
        }, status=status.HTTP_200_OK)

    existing = AccountDeletionRequest.objects.filter(
        user=user, status__in=['pending', 'processing']
    ).first()
    if existing:
        return Response({
            'message': 'You already have a pending deletion request.',
            'request_id': existing.id,
            'scheduled_deletion_date': existing.scheduled_deletion_date
        }, status=status.HTTP_200_OK)

    scheduled_date = timezone.now() + timedelta(days=30)
    deletion_request = AccountDeletionRequest.objects.create(
        user=user,
        deletion_type='account',
        reason='Requested via public deletion page',
        scheduled_deletion_date=scheduled_date,
    )

    logger.info(f"Public deletion request for {email}. Scheduled for {scheduled_date}")

    return Response({
        'message': 'Account deletion request submitted. Your account will be permanently '
                   'deleted within 30 days. To cancel, log into the app and go to Settings.',
        'request_id': deletion_request.id,
        'scheduled_deletion_date': scheduled_date,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def public_data_deletion_request(request):
    """
    Public endpoint (no auth required) to request deletion of specific data
    by providing email and data categories. Used by the public data deletion page.
    """
    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    categories = request.data.get('data_categories', [])
    if not categories:
        return Response({'error': 'Select at least one data category to delete.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({
            'message': 'If an account exists for this email, your data deletion request has been submitted.'
        }, status=status.HTTP_200_OK)

    # Perform the actual deletion
    handler = DeleteSpecificDataView()
    valid_categories = [c for c in categories if c in handler.DATA_HANDLERS or c == 'all']
    if not valid_categories:
        return Response({'error': 'Invalid data categories.'}, status=status.HTTP_400_BAD_REQUEST)

    if 'all' in valid_categories:
        valid_categories = list(handler.DATA_HANDLERS.keys())

    results = {}
    for category in valid_categories:
        handler_name = handler.DATA_HANDLERS.get(category)
        if handler_name:
            method = getattr(handler, handler_name, None)
            if method:
                results[category] = method(user)

    AccountDeletionRequest.objects.create(
        user=user,
        deletion_type='data',
        data_categories=valid_categories,
        reason='Requested via public data deletion page',
        status='completed',
        processed_at=timezone.now(),
    )

    logger.info(f"Public data deletion for {email}. Categories: {valid_categories}")

    return Response({
        'message': 'Your data deletion request has been processed. The selected data has been deleted. '
                   'Your account remains active.',
        'deleted': results
    }, status=status.HTTP_200_OK)
