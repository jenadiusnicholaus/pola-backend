"""
User Mention/Tagging Views - Handle @mentions in comments
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from authentication.models import PolaUser, UserPrivacySettings
from .models import CommentMention, HubComment
from .serializers import (
    UserMentionSerializer, CommentMentionSerializer,
    CreateCommentWithMentionsSerializer, UserPrivacySettingsSerializer,
    HubCommentSerializer
)
from .mention_notifications import notify_multiple_mentions


class UserMentionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for searching users to mention/tag
    
    Endpoints:
    - GET /api/v1/hubs/mentions/users/ - Search users for tagging
    - GET /api/v1/hubs/mentions/users/search/?q=john - Autocomplete search
    """
    serializer_class = UserMentionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']
    
    def get_queryset(self):
        """
        Return users that can be tagged
        Filters out users who don't allow tagging from anyone
        """
        queryset = PolaUser.objects.filter(is_active=True)
        
        # Exclude users who don't allow tagging at all
        # We'll check individual permissions in the serializer
        queryset = queryset.exclude(
            privacy_settings__allow_tagging='none'
        )
        
        return queryset.select_related('privacy_settings')
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search users for autocomplete mention suggestions
        
        Query params:
        - q: search query (name or email)
        - limit: max results (default 10)
        
        Returns: List of users matching search
        """
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 10))
        
        if not query or len(query) < 2:
            return Response({
                'error': 'Search query must be at least 2 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Search by first name, last name, or email
        users = self.get_queryset().filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:limit]
        
        serializer = self.get_serializer(users, many=True)
        return Response({
            'count': users.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def can_tag(self, request, pk=None):
        """
        Check if current user can tag a specific user
        
        Returns: {can_tag: true/false, reason: "..."}
        """
        user = self.get_object()
        
        if not hasattr(user, 'privacy_settings'):
            return Response({
                'can_tag': True,
                'reason': 'User has no privacy restrictions'
            })
        
        privacy = user.privacy_settings
        can_tag = privacy.can_be_tagged_by(request.user)
        
        reason = ''
        if not can_tag:
            if privacy.allow_tagging == 'none':
                reason = 'This user does not allow being tagged'
            elif privacy.allow_tagging == 'following':
                reason = 'This user only allows being tagged by people they follow'
        else:
            reason = 'You can tag this user'
        
        return Response({
            'can_tag': can_tag,
            'reason': reason
        })


class CommentMentionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user mentions
    
    Endpoints:
    - GET /api/v1/hubs/mentions/ - List all mentions for current user
    - GET /api/v1/hubs/mentions/unread/ - List unread mentions
    - POST /api/v1/hubs/mentions/{id}/mark_read/ - Mark mention as read
    - POST /api/v1/hubs/mentions/mark_all_read/ - Mark all mentions as read
    """
    serializer_class = CommentMentionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return mentions for current user"""
        # Handle swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return CommentMention.objects.none()
        
        return CommentMention.objects.filter(
            mentioned_user=self.request.user
        ).select_related(
            'comment', 'mentioned_user', 'mentioned_by'
        ).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread mentions for current user"""
        mentions = self.get_queryset().filter(is_read=False)
        
        page = self.paginate_queryset(mentions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(mentions, many=True)
        return Response({
            'count': mentions.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get mention statistics for current user"""
        mentions = self.get_queryset()
        
        return Response({
            'total_mentions': mentions.count(),
            'unread_mentions': mentions.filter(is_read=False).count(),
            'mentions_today': mentions.filter(
                created_at__date=timezone.now().date()
            ).count()
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific mention as read"""
        mention = self.get_object()
        
        if mention.mentioned_user != request.user:
            return Response({
                'error': 'You can only mark your own mentions as read'
            }, status=status.HTTP_403_FORBIDDEN)
        
        mention.mark_as_read()
        
        return Response({
            'message': 'Mention marked as read',
            'mention_id': mention.id
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all mentions as read for current user"""
        updated_count = self.get_queryset().filter(
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'message': f'{updated_count} mentions marked as read',
            'count': updated_count
        })


class CommentWithMentionsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for creating comments with user mentions
    
    Endpoints:
    - POST /api/v1/hubs/comments/ - Create comment with mentions
    - GET /api/v1/hubs/comments/ - List comments
    - GET /api/v1/hubs/comments/{id}/ - Get specific comment
    """
    serializer_class = HubCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return active comments"""
        queryset = HubComment.objects.filter(is_active=True)
        
        # Filter by hub_type
        hub_type = self.request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Filter by content
        content_id = self.request.query_params.get('content_id')
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        
        return queryset.select_related('author').prefetch_related('mentions')
    
    def get_serializer_class(self):
        """Use CreateCommentWithMentionsSerializer for creation"""
        if self.action == 'create':
            return CreateCommentWithMentionsSerializer
        return HubCommentSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create comment with mentions
        
        Request body:
        {
            "hub_type": "forum",
            "content": 123,
            "comment_text": "Hey @John, what do you think?",
            "mentioned_users": [456, 789],
            "parent_comment": null (optional, for replies)
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        
        # Return created comment with full details
        output_serializer = HubCommentSerializer(comment, context={'request': request})
        
        # Trigger notifications for mentioned users (if notification system exists)
        if hasattr(comment, 'mentions') and comment.mentions.exists():
            self._send_mention_notifications(comment)
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def _send_mention_notifications(self, comment):
        """
        Send notifications to mentioned users
        Uses the notification helper to send notifications
        """
        try:
            notify_multiple_mentions(comment)
        except Exception as e:
            # Log error but don't fail the request
            print(f"[ERROR] Failed to send mention notifications: {str(e)}")


class UserPrivacySettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for managing user privacy settings
    
    Endpoints:
    - GET /api/v1/hubs/privacy/ - Get current user's privacy settings
    - PUT /api/v1/hubs/privacy/ - Update privacy settings
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get current user's privacy settings"""
        settings, created = UserPrivacySettings.objects.get_or_create(
            user=request.user
        )
        
        serializer = UserPrivacySettingsSerializer(settings)
        return Response(serializer.data)
    
    def update(self, request):
        """Update privacy settings"""
        settings, created = UserPrivacySettings.objects.get_or_create(
            user=request.user
        )
        
        serializer = UserPrivacySettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        # Update settings
        for field, value in serializer.validated_data.items():
            setattr(settings, field, value)
        settings.save()
        
        return Response({
            'message': 'Privacy settings updated successfully',
            'settings': UserPrivacySettingsSerializer(settings).data
        })
