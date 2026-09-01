from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import BlockedUser, UserReport
from .moderation_serializers import (
    BlockedUserSerializer,
    BlockUserSerializer,
    UserReportSerializer,
    CreateReportSerializer,
)

User = get_user_model()


class BlockUserView(APIView):
    """Block a user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        reason = serializer.validated_data.get('reason', '')

        try:
            blocked_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if blocked_user == request.user:
            return Response({'error': 'You cannot block yourself'}, status=status.HTTP_400_BAD_REQUEST)

        obj, created = BlockedUser.objects.get_or_create(
            blocker=request.user,
            blocked=blocked_user,
            defaults={'reason': reason}
        )

        if not created:
            return Response({'message': 'User is already blocked', 'blocked': True}, status=status.HTTP_200_OK)

        return Response({
            'message': 'User blocked successfully',
            'blocked': True,
            'blocked_user_id': blocked_user.id,
            'blocked_user_email': blocked_user.email
        }, status=status.HTTP_201_CREATED)


class UnblockUserView(APIView):
    """Unblock a user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        try:
            blocked = BlockedUser.objects.get(blocker=request.user, blocked_id=user_id)
        except BlockedUser.DoesNotExist:
            return Response({'error': 'User is not blocked'}, status=status.HTTP_404_NOT_FOUND)

        blocked.delete()
        return Response({'message': 'User unblocked successfully', 'blocked': False}, status=status.HTTP_200_OK)


class BlockedUsersListView(generics.ListAPIView):
    """List all users blocked by the current user."""
    serializer_class = BlockedUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlockedUser.objects.filter(blocker=self.request.user)


class CheckBlockedView(APIView):
    """Check if a user is blocked by the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        is_blocked = BlockedUser.objects.filter(
            blocker=request.user, blocked_id=user_id
        ).exists()
        return Response({'is_blocked': is_blocked}, status=status.HTTP_200_OK)


class ReportUserView(APIView):
    """Report a user or user-generated content."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        reported_user_id = data.get('reported_user_id')

        reported_user = None
        if reported_user_id:
            try:
                reported_user = User.objects.get(id=reported_user_id)
            except User.DoesNotExist:
                return Response({'error': 'Reported user not found'}, status=status.HTTP_404_NOT_FOUND)

            if reported_user == request.user:
                return Response({'error': 'You cannot report yourself'}, status=status.HTTP_400_BAD_REQUEST)

        report = UserReport.objects.create(
            reporter=request.user,
            reported_user=reported_user,
            report_type=data.get('report_type', 'other'),
            description=data.get('description', ''),
            content_type=data.get('content_type', ''),
            content_id=data.get('content_id', ''),
        )

        return Response({
            'message': 'Report submitted successfully',
            'report_id': report.id,
            'status': report.status
        }, status=status.HTTP_201_CREATED)


class MyReportsListView(generics.ListAPIView):
    """List reports made by the current user."""
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserReport.objects.filter(reporter=self.request.user)


class ReportDetailView(generics.RetrieveAPIView):
    """Get details of a specific report."""
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserReport.objects.filter(reporter=self.request.user)
