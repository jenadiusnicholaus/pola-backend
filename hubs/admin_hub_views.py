"""
Admin Hub Management Views
Comprehensive admin API for managing all hub content (Advocates, Students, Forum)
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Q, Avg, Sum
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
# import csv  # Export functionality disabled
# Excel export functionality removed for simplification
# from openpyxl import Workbook
# from openpyxl.styles import Font, PatternFill, Alignment

from documents.models import LearningMaterial, LearningMaterialPurchase, LecturerFollow, MaterialQuestion, MaterialRating
from .models import (
    HubComment, ContentLike, ContentBookmark, HubMessage
)
from .serializers import (
    HubContentSerializer, HubCommentSerializer,
    LecturerFollowSerializer, MaterialQuestionSerializer,
    MaterialRatingSerializer, HubMessageSerializer,
    # Admin CRUD Serializers
    AdminContentCreateSerializer, AdminContentUpdateSerializer,
    AdminContentDetailSerializer, AdminContentListSerializer,
    BulkActionSerializer
)


class AdminHubContentViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing all hub content (FULL CRUD)
    
    Provides complete CRUD operations, moderation, analytics, and bulk actions
    for content across all hubs (Advocates, Students, Forum, Legal Education).
    
    Features:
    - ✅ CREATE: Post news, discussions, announcements, articles
    - ✅ READ: View content with full details and engagement stats
    - ✅ UPDATE: Edit content, change status, moderate
    - ✅ DELETE: Remove content
    - ✅ BULK ACTIONS: Pin, approve, activate multiple items
    - ✅ ANALYTICS: Engagement stats, trending, top content
    - ✅ EXPORT: CSV/Excel export functionality
    
    Endpoints:
    - POST   /api/v1/admin/hubs/hub-content/          - Create content
    - GET    /api/v1/admin/hubs/hub-content/          - List all content
    - GET    /api/v1/admin/hubs/hub-content/{id}/     - Get specific content
    - PUT    /api/v1/admin/hubs/hub-content/{id}/     - Update content
    - PATCH  /api/v1/admin/hubs/hub-content/{id}/     - Partial update
    - DELETE /api/v1/admin/hubs/hub-content/{id}/     - Delete content
    - POST   /api/v1/admin/hubs/hub-content/bulk_action/ - Bulk operations
    """
    queryset = LearningMaterial.objects.all()
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'content', 'uploader__email', 'uploader__first_name', 'uploader__last_name']
    ordering_fields = ['created_at', 'views_count', 'downloads_count', 'likes_count', 'price']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action
        
        - CREATE: AdminContentCreateSerializer (simplified with defaults)
        - UPDATE: AdminContentUpdateSerializer (all editable fields)
        - RETRIEVE: AdminContentDetailSerializer (full details + stats)
        - LIST: AdminContentListSerializer (optimized for listing)
        """
        if self.action == 'create':
            return AdminContentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminContentUpdateSerializer
        elif self.action == 'retrieve':
            return AdminContentDetailSerializer
        elif self.action == 'list':
            return AdminContentListSerializer
        return HubContentSerializer
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by hub_type and other params"""
        queryset = super().get_queryset().select_related(
            'uploader', 'uploader__verification'
        ).prefetch_related('likes', 'comments', 'bookmarks', 'ratings')
        
        # Filter by hub type (support both direct value and object format)
        hub_type = self.request.query_params.get('hub_type') or self.request.query_params.get('hub_type[value]')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type') or self.request.query_params.get('content_type[value]')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Filter by uploader type
        uploader_type = self.request.query_params.get('uploader_type') or self.request.query_params.get('uploader_type[value]')
        if uploader_type:
            queryset = queryset.filter(uploader_type=uploader_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by pinned status
        is_pinned = self.request.query_params.get('is_pinned')
        if is_pinned is not None:
            queryset = queryset.filter(is_pinned=is_pinned.lower() == 'true')
        
        # Filter by downloadable
        is_downloadable = self.request.query_params.get('is_downloadable')
        if is_downloadable is not None:
            queryset = queryset.filter(is_downloadable=is_downloadable.lower() == 'true')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filter by uploader
        uploader_id = self.request.query_params.get('uploader_id')
        if uploader_id:
            queryset = queryset.filter(uploader_id=uploader_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create new content (POST)
        
        Admin can create news, discussions, announcements, articles, etc.
        Automatically sets admin as uploader and approves content.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return with detailed serializer
        instance = serializer.instance
        detail_serializer = AdminContentDetailSerializer(instance, context={'request': request})
        
        return Response(
            {
                'message': 'Content created successfully',
                'data': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Full update of content (PUT)
        
        Update all fields of existing content.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return with detailed serializer
        detail_serializer = AdminContentDetailSerializer(instance, context={'request': request})
        
        return Response({
            'message': 'Content updated successfully',
            'data': detail_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete content (DELETE)
        
        Permanently removes content and all associated data.
        """
        instance = self.get_object()
        content_title = instance.title
        content_id = instance.id
        
        self.perform_destroy(instance)
        
        return Response({
            'message': f'Content "{content_title}" (ID: {content_id}) deleted successfully'
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        method='post',
        request_body=BulkActionSerializer,
        operation_description="""
        Perform bulk actions on multiple content items
        
        Actions:
        - pin: Pin content to top of feed
        - unpin: Remove from pinned position
        - approve: Approve user-submitted content
        - reject: Reject/unapprove content
        - activate: Make content visible
        - deactivate: Hide content from users
        - delete: Permanently delete content
        
        Example:
        {
            "content_ids": [1, 2, 3, 4, 5],
            "action": "pin"
        }
        """,
        responses={
            200: openapi.Response(
                description="Bulk action completed",
                examples={
                    "application/json": {
                        "message": "Bulk action completed successfully",
                        "action": "pin",
                        "affected_count": 5,
                        "content_ids": [1, 2, 3, 4, 5]
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """
        Perform bulk actions on multiple content items
        
        POST /api/v1/admin/hubs/hub-content/bulk_action/
        {
            "content_ids": [1, 2, 3],
            "action": "pin|unpin|approve|reject|activate|deactivate|delete"
        }
        """
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        content_ids = serializer.validated_data['content_ids']
        action_type = serializer.validated_data['action']
        
        queryset = LearningMaterial.objects.filter(id__in=content_ids)
        count = queryset.count()
        
        # Perform the action
        if action_type == 'pin':
            queryset.update(is_pinned=True)
            message = f'{count} item(s) pinned successfully'
        
        elif action_type == 'unpin':
            queryset.update(is_pinned=False)
            message = f'{count} item(s) unpinned successfully'
        
        elif action_type == 'approve':
            queryset.update(is_approved=True)
            message = f'{count} item(s) approved successfully'
        
        elif action_type == 'reject':
            queryset.update(is_approved=False)
            message = f'{count} item(s) rejected successfully'
        
        elif action_type == 'activate':
            queryset.update(is_active=True)
            message = f'{count} item(s) activated successfully'
        
        elif action_type == 'deactivate':
            queryset.update(is_active=False)
            message = f'{count} item(s) deactivated successfully'
        
        elif action_type == 'delete':
            queryset.delete()
            message = f'{count} item(s) deleted successfully'
        
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': message,
            'action': action_type,
            'affected_count': count,
            'content_ids': content_ids
        })

    @swagger_auto_schema(
        method='post',
        operation_description="Pin content to top of hub feed",
        responses={200: 'Content pinned successfully'}
    )
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin content to top"""
        content = self.get_object()
        content.is_pinned = True
        content.save(update_fields=['is_pinned'])
        return Response({
            'message': 'Content pinned successfully',
            'id': content.id,
            'is_pinned': True
        })

    @swagger_auto_schema(
        method='post',
        operation_description="Unpin content from top of hub feed",
        responses={200: 'Content unpinned successfully'}
    )
    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """Unpin content"""
        content = self.get_object()
        content.is_pinned = False
        content.save(update_fields=['is_pinned'])
        return Response({
            'message': 'Content unpinned successfully',
            'id': content.id,
            'is_pinned': False
        })

    @swagger_auto_schema(
        method='post',
        operation_description="Toggle content active status",
        responses={200: 'Content status toggled'}
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle active status"""
        content = self.get_object()
        content.is_active = not content.is_active
        content.save(update_fields=['is_active'])
        return Response({
            'message': 'Content status toggled',
            'id': content.id,
            'is_active': content.is_active
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='Array of content IDs to delete'
                )
            },
            required=['content_ids']
        ),
        responses={200: 'Content deleted successfully'}
    )
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete content"""
        content_ids = request.data.get('content_ids', [])
        if not content_ids:
            return Response({'error': 'No content IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = LearningMaterial.objects.filter(id__in=content_ids).delete()[0]
        return Response({
            'message': f'{deleted_count} content items deleted',
            'deleted_count': deleted_count
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                ),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            },
            required=['content_ids', 'is_active']
        ),
        responses={200: 'Content status updated'}
    )
    @action(detail=False, methods=['post'])
    def bulk_toggle_active(self, request):
        """Bulk toggle active status"""
        content_ids = request.data.get('content_ids', [])
        is_active = request.data.get('is_active')
        
        if not content_ids:
            return Response({'error': 'No content IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = LearningMaterial.objects.filter(
            id__in=content_ids
        ).update(is_active=is_active)
        
        return Response({
            'message': f'{updated_count} content items updated',
            'updated_count': updated_count,
            'is_active': is_active
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                ),
                'is_pinned': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            },
            required=['content_ids', 'is_pinned']
        ),
        responses={200: 'Content pinned status updated'}
    )
    @action(detail=False, methods=['post'])
    def bulk_pin(self, request):
        """Bulk pin/unpin content"""
        content_ids = request.data.get('content_ids', [])
        is_pinned = request.data.get('is_pinned')
        
        if not content_ids:
            return Response({'error': 'No content IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = LearningMaterial.objects.filter(
            id__in=content_ids
        ).update(is_pinned=is_pinned)
        
        return Response({
            'message': f'{updated_count} content items updated',
            'updated_count': updated_count,
            'is_pinned': is_pinned
        })

    @swagger_auto_schema(
        method='get',
        operation_description="Get comprehensive hub statistics",
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Days to look back (default: 30)'),
        ],
        responses={200: 'Statistics retrieved'}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive statistics"""
        hub_type = request.query_params.get('hub_type')
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = LearningMaterial.objects.all()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        recent_queryset = queryset.filter(created_at__gte=start_date)
        
        # Basic counts
        stats = {
            'total_content': queryset.count(),
            'active_content': queryset.filter(is_active=True).count(),
            'inactive_content': queryset.filter(is_active=False).count(),
            'pinned_content': queryset.filter(is_pinned=True).count(),
            'recent_content': recent_queryset.count(),
            
            # By hub type
            'by_hub_type': {},
            
            # By content type
            'by_content_type': {},
            
            # By uploader type
            'by_uploader_type': {},
            
            # Engagement
            'total_likes': ContentLike.objects.filter(content__in=queryset).count(),
            'total_comments': HubComment.objects.filter(content__in=queryset).count(),
            'total_bookmarks': ContentBookmark.objects.filter(content__in=queryset).count(),
            
            # Students Hub specific
            'total_purchases': 0,
            'total_revenue': 0,
            'total_questions': 0,
            'total_ratings': 0,
            'average_rating': 0,
            
            # Recent activity
            'recent_likes': ContentLike.objects.filter(
                content__in=queryset, created_at__gte=start_date
            ).count(),
            'recent_comments': HubComment.objects.filter(
                content__in=queryset, created_at__gte=start_date
            ).count(),
        }
        
        # Hub type breakdown
        for ht in queryset.values('hub_type').annotate(count=Count('id')):
            stats['by_hub_type'][ht['hub_type']] = ht['count']
        
        # Content type breakdown
        for ct in queryset.values('content_type').annotate(count=Count('id')):
            stats['by_content_type'][ct['content_type']] = ct['count']
        
        # Uploader type breakdown
        for ut in queryset.values('uploader_type').annotate(count=Count('id')):
            stats['by_uploader_type'][ut['uploader_type']] = ut['count']
        
        # Students Hub specific stats
        if not hub_type or hub_type == 'students':
            students_content = queryset.filter(hub_type='students')
            purchases = LearningMaterialPurchase.objects.filter(material__in=students_content)
            
            stats['total_purchases'] = purchases.count()
            stats['total_revenue'] = float(purchases.aggregate(
                total=Sum('material__price')
            )['total'] or 0)
            stats['total_questions'] = MaterialQuestion.objects.filter(
                material__in=students_content
            ).count()
            
            ratings_data = MaterialRating.objects.filter(
                material__in=students_content
            ).aggregate(
                count=Count('id'),
                avg=Avg('rating')
            )
            stats['total_ratings'] = ratings_data['count']
            stats['average_rating'] = float(ratings_data['avg'] or 0)
        
        return Response(stats)

    @swagger_auto_schema(
        method='get',
        operation_description="Get top content by views/likes/downloads",
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('metric', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description='views_count, likes_count, downloads_count, or comments_count'),
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Number of items (default: 10)'),
        ],
        responses={200: HubContentSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def top_content(self, request):
        """Get top performing content"""
        hub_type = request.query_params.get('hub_type')
        metric = request.query_params.get('metric', 'views_count')
        limit = int(request.query_params.get('limit', 10))
        
        queryset = self.get_queryset()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Annotate with engagement counts if needed
        if metric == 'likes_count':
            queryset = queryset.annotate(likes_count=Count('likes'))
        elif metric == 'comments_count':
            queryset = queryset.annotate(comments_count=Count('comments'))
        
        top_content = queryset.order_by(f'-{metric}')[:limit]
        serializer = self.get_serializer(top_content, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Get trending content",
        operation_description="Get content with highest engagement in the last N days",
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='Days to look back (default: 7)'),
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='Number of items (default: 10)'),
        ],
        responses={200: 'Trending content with engagement scores'}
    )
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending content based on recent engagement"""
        hub_type = request.query_params.get('hub_type')
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        
        since_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Calculate engagement score based on recent activity
        queryset = queryset.annotate(
            recent_likes=Count('likes', filter=Q(likes__created_at__gte=since_date)),
            recent_comments=Count('comments', filter=Q(comments__created_at__gte=since_date)),
            recent_bookmarks=Count('bookmarks', filter=Q(bookmarks__created_at__gte=since_date))
        ).annotate(
            engagement_score=Count('likes', filter=Q(likes__created_at__gte=since_date)) * 2 +
                           Count('comments', filter=Q(comments__created_at__gte=since_date)) * 3 +
                           Count('bookmarks', filter=Q(bookmarks__created_at__gte=since_date)) * 4
        ).filter(engagement_score__gt=0).order_by('-engagement_score')[:limit]
        
        data = []
        for content in queryset:
            serialized = self.get_serializer(content).data
            serialized['trending_stats'] = {
                'recent_likes': content.recent_likes,
                'recent_comments': content.recent_comments,
                'recent_bookmarks': content.recent_bookmarks,
                'engagement_score': content.engagement_score,
                'trending_period_days': days
            }
            data.append(serialized)
        
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Get engagement trends over time",
        operation_description="Get daily engagement metrics for the last N days",
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='Days to analyze (default: 30)'),
        ],
        responses={200: 'Daily engagement metrics'}
    )
    @action(detail=False, methods=['get'])
    def engagement_trends(self, request):
        """Get engagement trends over time"""
        hub_type = request.query_params.get('hub_type')
        days = int(request.query_params.get('days', 30))
        
        since_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Get daily engagement data
        from django.db.models.functions import TruncDate
        
        likes_by_day = ContentLike.objects.filter(
            content__in=queryset,
            created_at__gte=since_date
        ).annotate(date=TruncDate('created_at')).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        comments_by_day = HubComment.objects.filter(
            content__in=queryset,
            created_at__gte=since_date
        ).annotate(date=TruncDate('created_at')).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        bookmarks_by_day = ContentBookmark.objects.filter(
            content__in=queryset,
            created_at__gte=since_date
        ).annotate(date=TruncDate('created_at')).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Combine data
        trends = {}
        for item in likes_by_day:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str not in trends:
                trends[date_str] = {'date': date_str, 'likes': 0, 'comments': 0, 'bookmarks': 0}
            trends[date_str]['likes'] = item['count']
        
        for item in comments_by_day:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str not in trends:
                trends[date_str] = {'date': date_str, 'likes': 0, 'comments': 0, 'bookmarks': 0}
            trends[date_str]['comments'] = item['count']
        
        for item in bookmarks_by_day:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str not in trends:
                trends[date_str] = {'date': date_str, 'likes': 0, 'comments': 0, 'bookmarks': 0}
            trends[date_str]['bookmarks'] = item['count']
        
        # Sort by date
        sorted_trends = sorted(trends.values(), key=lambda x: x['date'])
        
        return Response({
            'period_days': days,
            'hub_type': hub_type or 'all',
            'daily_trends': sorted_trends,
            'summary': {
                'total_likes': sum(t['likes'] for t in sorted_trends),
                'total_comments': sum(t['comments'] for t in sorted_trends),
                'total_bookmarks': sum(t['bookmarks'] for t in sorted_trends),
                'average_daily_likes': sum(t['likes'] for t in sorted_trends) / max(len(sorted_trends), 1),
                'average_daily_comments': sum(t['comments'] for t in sorted_trends) / max(len(sorted_trends), 1),
                'average_daily_bookmarks': sum(t['bookmarks'] for t in sorted_trends) / max(len(sorted_trends), 1),
            }
        })

    @swagger_auto_schema(
        operation_summary="Get top contributors",
        operation_description="Get users with most content uploads and engagement",
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='Number of users (default: 10)'),
        ],
        responses={200: 'Top contributors with stats'}
    )
    @action(detail=False, methods=['get'])
    def top_contributors(self, request):
        """Get top content contributors with their stats"""
        hub_type = request.query_params.get('hub_type')
        limit = int(request.query_params.get('limit', 10))
        
        queryset = self.get_queryset()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Get top uploaders
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        contributors = User.objects.filter(
            id__in=queryset.values_list('uploader_id', flat=True)
        ).annotate(
            content_count=Count('learning_materials', filter=Q(learning_materials__in=queryset)),
            total_views=Sum('learning_materials__views_count', filter=Q(learning_materials__in=queryset)),
            total_likes=Count('learning_materials__likes', filter=Q(learning_materials__in=queryset)),
            total_downloads=Sum('learning_materials__downloads_count', filter=Q(learning_materials__in=queryset)),
        ).filter(content_count__gt=0).order_by('-content_count')[:limit]
        
        data = []
        for user in contributors:
            data.append({
                'user_id': user.id,
                'user_name': user.get_full_name() or user.email,
                'user_email': user.email,
                'content_count': user.content_count,
                'total_views': user.total_views or 0,
                'total_likes': user.total_likes or 0,
                'total_downloads': user.total_downloads or 0,
                'average_views_per_content': (user.total_views or 0) / max(user.content_count, 1),
            })
        
        return Response(data)

    @swagger_auto_schema(
        operation_summary="Get content performance metrics",
        operation_description="Get detailed performance metrics for specific content",
        responses={200: 'Comprehensive performance metrics'}
    )
    @action(detail=True, methods=['get'])
    def performance_metrics(self, request, pk=None):
        """Get comprehensive performance metrics for content"""
        content = self.get_object()
        
        # Basic metrics
        total_engagement = (
            (content.views_count or 0) +
            (content.likes_count or 0) * 2 +
            (content.comments.count()) * 3 +
            (content.bookmarks.count()) * 4 +
            (content.downloads_count or 0) * 2
        )
        
        # Time-based metrics
        days_since_creation = (timezone.now() - content.created_at).days or 1
        
        # Engagement rate calculations
        views = content.views_count or 1  # Avoid division by zero
        likes_rate = ((content.likes_count or 0) / views) * 100
        comments_rate = (content.comments.count() / views) * 100
        bookmarks_rate = (content.bookmarks.count() / views) * 100
        download_rate = ((content.downloads_count or 0) / views) * 100 if content.is_downloadable else 0
        
        # Revenue metrics (for students hub)
        revenue = 0
        purchases_count = 0
        if content.hub_type == 'students' and content.content_type == 'document':
            purchases = LearningMaterialPurchase.objects.filter(material=content)
            purchases_count = purchases.count()
            revenue = float(content.price or 0) * purchases_count
        
        # Recent engagement (last 7 days)
        last_week = timezone.now() - timedelta(days=7)
        recent_likes = ContentLike.objects.filter(content=content, created_at__gte=last_week).count()
        recent_comments = HubComment.objects.filter(content=content, created_at__gte=last_week).count()
        recent_bookmarks = ContentBookmark.objects.filter(content=content, created_at__gte=last_week).count()
        
        # Rating metrics (if applicable)
        avg_rating = 0
        rating_count = 0
        if content.hub_type == 'students':
            ratings = MaterialRating.objects.filter(material=content)
            rating_count = ratings.count()
            if rating_count > 0:
                avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
        
        return Response({
            'content_id': content.id,
            'content_title': content.title,
            'hub_type': content.hub_type,
            'created_at': content.created_at,
            'days_since_creation': days_since_creation,
            
            # Core metrics
            'views': content.views_count or 0,
            'likes': content.likes_count or 0,
            'comments': content.comments.count(),
            'bookmarks': content.bookmarks.count(),
            'downloads': content.downloads_count or 0,
            'shares': content.shares_count or 0,
            
            # Engagement rates
            'engagement_rates': {
                'likes_rate': round(likes_rate, 2),
                'comments_rate': round(comments_rate, 2),
                'bookmarks_rate': round(bookmarks_rate, 2),
                'download_rate': round(download_rate, 2),
            },
            
            # Performance scores
            'scores': {
                'total_engagement_score': total_engagement,
                'daily_average_views': round((content.views_count or 0) / days_since_creation, 2),
                'engagement_per_view': round(total_engagement / views, 2),
            },
            
            # Recent activity (7 days)
            'recent_activity': {
                'likes': recent_likes,
                'comments': recent_comments,
                'bookmarks': recent_bookmarks,
            },
            
            # Revenue (if applicable)
            'monetization': {
                'price': float(content.price or 0),
                'purchases': purchases_count,
                'total_revenue': revenue,
            } if content.hub_type == 'students' and content.content_type == 'document' else None,
            
            # Rating (if applicable)
            'rating': {
                'average': round(avg_rating, 2) if avg_rating else 0,
                'count': rating_count,
            } if content.hub_type == 'students' else None,
        })

    @swagger_auto_schema(
        method='get',
        operation_description="Get all comments for specific content",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        responses={200: HubCommentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get all comments for this content"""
        content = self.get_object()
        comments = HubComment.objects.filter(content=content).select_related(
            'author'
        ).prefetch_related('likes', 'replies').order_by('-created_at')
        
        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        paginated_comments = paginator.paginate_queryset(comments, request)
        
        serializer = HubCommentSerializer(paginated_comments, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        method='get',
        operation_description="Get all users who liked this content",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        responses={200: openapi.Response(
            description="List of users who liked the content",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_email': openapi.Schema(type=openapi.TYPE_STRING),
                                'user_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    )
                }
            )
        )}
    )
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        """Get all users who liked this content"""
        content = self.get_object()
        likes = ContentLike.objects.filter(content=content).select_related(
            'user'
        ).order_by('-created_at')
        
        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 50))
        paginated_likes = paginator.paginate_queryset(likes, request)
        
        # Serialize likes data
        likes_data = [{
            'id': like.id,
            'user_id': like.user.id,
            'user_email': like.user.email,
            'user_name': f"{like.user.first_name} {like.user.last_name}".strip() or like.user.email,
            'created_at': like.created_at.isoformat(),
        } for like in paginated_likes]
        
        return paginator.get_paginated_response(likes_data)

    @swagger_auto_schema(
        method='get',
        operation_description="Get all users who bookmarked this content",
        responses={200: openapi.Response(description="List of users who bookmarked")}
    )
    @action(detail=True, methods=['get'])
    def bookmarks(self, request, pk=None):
        """Get all users who bookmarked this content"""
        content = self.get_object()
        bookmarks = ContentBookmark.objects.filter(content=content).select_related(
            'user'
        ).order_by('-created_at')
        
        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 50))
        paginated_bookmarks = paginator.paginate_queryset(bookmarks, request)
        
        bookmarks_data = [{
            'id': bookmark.id,
            'user_id': bookmark.user.id,
            'user_email': bookmark.user.email,
            'user_name': f"{bookmark.user.first_name} {bookmark.user.last_name}".strip() or bookmark.user.email,
            'created_at': bookmark.created_at.isoformat(),
        } for bookmark in paginated_bookmarks]
        
        return paginator.get_paginated_response(bookmarks_data)

    @swagger_auto_schema(
        method='get',
        operation_description="Get engagement summary (comments, likes, bookmarks counts and recent activity)",
        responses={200: openapi.Response(
            description="Engagement summary",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_comments': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_likes': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_bookmarks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'recent_comments': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                    'recent_likes': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    ),
                }
            )
        )}
    )
    @action(detail=True, methods=['get'])
    def engagement(self, request, pk=None):
        """Get detailed engagement summary for content"""
        content = self.get_object()
        
        # Get counts
        comments_count = HubComment.objects.filter(content=content).count()
        likes_count = ContentLike.objects.filter(content=content).count()
        bookmarks_count = ContentBookmark.objects.filter(content=content).count()
        
        # Get recent activity (last 10)
        recent_comments = HubComment.objects.filter(
            content=content
        ).select_related('author').order_by('-created_at')[:10]
        
        recent_likes = ContentLike.objects.filter(
            content=content
        ).select_related('user').order_by('-created_at')[:10]
        
        # Serialize recent activity
        comments_data = HubCommentSerializer(recent_comments, many=True, context={'request': request}).data
        
        likes_data = [{
            'user_id': like.user.id,
            'user_name': f"{like.user.first_name} {like.user.last_name}".strip() or like.user.email,
            'created_at': like.created_at.isoformat(),
        } for like in recent_likes]
        
        return Response({
            'total_comments': comments_count,
            'total_likes': likes_count,
            'total_bookmarks': bookmarks_count,
            'recent_comments': comments_data,
            'recent_likes': likes_data,
        })

    # Export functionality disabled for simplification
    # @swagger_auto_schema(
    #     operation_summary="Export content data",
    #     operation_description="Export content data to CSV or Excel format",
    #     manual_parameters=[
    #         openapi.Parameter(
    #             'format',
    #             openapi.IN_QUERY,
    #             description="Export format: csv or excel",
    #             type=openapi.TYPE_STRING,
    #             enum=['csv', 'excel'],
    #             required=False,
    #             default='csv'
    #         ),
    #         openapi.Parameter(
    #             'hub_type',
    #             openapi.IN_QUERY,
    #             description="Filter by hub type",
    #             type=openapi.TYPE_STRING,
    #             required=False
    #         ),
    #     ]
    # )
    # @action(detail=False, methods=['get'])
    # def export(self, request):
    #     """Export content data to CSV or Excel"""
    #     export_format = request.query_params.get('format', 'csv')
    #     queryset = self.filter_queryset(self.get_queryset())
    #     
    #     if export_format == 'excel':
    #         return self._export_excel(queryset)
    #     else:
    #         return self._export_csv(queryset)

    # Export functionality removed for simplification (no openpyxl dependency needed)
    pass
    #     # \"\"\"Export to CSV format\"\"\"
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = f'attachment; filename="hub_content_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
    #     writer = csv.writer(response)
    #     # Header
    #     writer.writerow([
    #         'ID', 'Title', 'Hub Type', 'Content Type', 'Uploader', 'Uploader Email',
    #         'Views', 'Downloads', 'Likes', 'Comments', 'Bookmarks', 'Price',
    #         'Is Active', 'Is Pinned', 'Created At', 'Updated At'
    #     ])
        
    #     # Data rows
    #     for content in queryset:
    #         writer.writerow([
    #             content.id,
    #             content.title or 'N/A',
    #             content.get_hub_type_display(),
    #             content.get_content_type_display(),
    #             content.uploader.get_full_name() or content.uploader.email,
    #             content.uploader.email,
    #             content.views_count or 0,
    #             content.downloads_count or 0,
    #             content.likes_count or 0,
    #             content.comments.count(),
    #             content.bookmarks.count(),
    #             content.price or 0,
    #             'Yes' if content.is_active else 'No',
    #             'Yes' if content.is_pinned else 'No',
    #             content.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #             content.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     return response

    # def _export_excel(self, queryset):
    #     """Export to Excel format"""
    #     wb = Workbook()
    #     ws = wb.active
    #     ws.title = "Hub Content"
        
    #     # Styling
    #     header_font = Font(bold=True, color="FFFFFF")
    #     header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    #     header_alignment = Alignment(horizontal="center", vertical="center")
        
    #     # Headers
    #     headers = [
    #         'ID', 'Title', 'Hub Type', 'Content Type', 'Uploader', 'Uploader Email',
    #         'Views', 'Downloads', 'Likes', 'Comments', 'Bookmarks', 'Price',
    #         'Is Active', 'Is Pinned', 'Created At', 'Updated At'
    #     ]
        
    #     for col_num, header in enumerate(headers, 1):
    #         cell = ws.cell(row=1, column=col_num, value=header)
    #         cell.font = header_font
    #         cell.fill = header_fill
    #         cell.alignment = header_alignment
        
    #     # Data rows
    #     for row_num, content in enumerate(queryset, 2):
    #         ws.cell(row=row_num, column=1, value=content.id)
    #         ws.cell(row=row_num, column=2, value=content.title or 'N/A')
    #         ws.cell(row=row_num, column=3, value=content.get_hub_type_display())
    #         ws.cell(row=row_num, column=4, value=content.get_content_type_display())
    #         ws.cell(row=row_num, column=5, value=content.uploader.get_full_name() or content.uploader.email)
    #         ws.cell(row=row_num, column=6, value=content.uploader.email)
    #         ws.cell(row=row_num, column=7, value=content.views_count or 0)
    #         ws.cell(row=row_num, column=8, value=content.downloads_count or 0)
    #         ws.cell(row=row_num, column=9, value=content.likes_count or 0)
    #         ws.cell(row=row_num, column=10, value=content.comments.count())
    #         ws.cell(row=row_num, column=11, value=content.bookmarks.count())
    #         ws.cell(row=row_num, column=12, value=float(content.price or 0))
    #         ws.cell(row=row_num, column=13, value='Yes' if content.is_active else 'No')
    #         ws.cell(row=row_num, column=14, value='Yes' if content.is_pinned else 'No')
    #         ws.cell(row=row_num, column=15, value=content.created_at.strftime('%Y-%m-%d %H:%M:%S'))
    #         ws.cell(row=row_num, column=16, value=content.updated_at.strftime('%Y-%m-%d %H:%M:%S'))
        
    #     # Adjust column widths
    #     for col in ws.columns:
    #         max_length = 0
    #         column = col[0].column_letter
    #         for cell in col:
    #             try:
    #                 if len(str(cell.value)) > max_length:
    #                     max_length = len(str(cell.value))
    #             except:
    #                 pass
    #         adjusted_width = min(max_length + 2, 50)
    #         ws.column_dimensions[column].width = adjusted_width
        
    #     # Save to response
    #     response = HttpResponse(
    #         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     )
    #     response['Content-Disposition'] = f'attachment; filename="hub_content_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    #     wb.save(response)
        
    #     return response

    # @swagger_auto_schema(
    #     operation_summary="Export engagement data for content",
    #     operation_description="Export comments, likes, and bookmarks data",
    #     manual_parameters=[
    #         openapi.Parameter(
    #             'format',
    #             openapi.IN_QUERY,
    #             description="Export format: csv or excel",
    #             type=openapi.TYPE_STRING,
    #             enum=['csv', 'excel'],
    #             required=False,
    #             default='csv'
    #         ),
    #     ]
    # )
    # @action(detail=True, methods=['get'])
    # def export_engagement(self, request, pk=None):
    #     """Export engagement data for specific content"""
    #     content = self.get_object()
    #     export_format = request.query_params.get('format', 'csv')
        
    #     if export_format == 'excel':
    #         return self._export_engagement_excel(content)
    #     else:
    #         return self._export_engagement_csv(content)

    # def _export_engagement_csv(self, content):
    #     """Export engagement to CSV"""
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = f'attachment; filename="engagement_content_{content.id}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
    #     writer = csv.writer(response)
        
    #     # Comments section
    #     writer.writerow(['COMMENTS'])
    #     writer.writerow(['ID', 'Author', 'Email', 'Comment', 'Likes', 'Created At'])
    #     comments = HubComment.objects.filter(content=content).select_related('author')
    #     for comment in comments:
    #         writer.writerow([
    #             comment.id,
    #             comment.author.get_full_name() or comment.author.email,
    #             comment.author.email,
    #             comment.comment_text,
    #             comment.likes_count or 0,
    #             comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     writer.writerow([])  # Empty row
        
    #     # Likes section
    #     writer.writerow(['LIKES'])
    #     writer.writerow(['ID', 'User', 'Email', 'Created At'])
    #     likes = ContentLike.objects.filter(content=content).select_related('user')
    #     for like in likes:
    #         writer.writerow([
    #             like.id,
    #             like.user.get_full_name() or like.user.email,
    #             like.user.email,
    #             like.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     writer.writerow([])  # Empty row
        
    #     # Bookmarks section
    #     writer.writerow(['BOOKMARKS'])
    #     writer.writerow(['ID', 'User', 'Email', 'Created At'])
    #     bookmarks = ContentBookmark.objects.filter(content=content).select_related('user')
    #     for bookmark in bookmarks:
    #         writer.writerow([
    #             bookmark.id,
    #             bookmark.user.get_full_name() or bookmark.user.email,
    #             bookmark.user.email,
    #             bookmark.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     return response

    # def _export_engagement_excel(self, content):
    #     """Export engagement to Excel with multiple sheets"""
    #     wb = Workbook()
        
    #     # Styling
    #     header_font = Font(bold=True, color="FFFFFF")
    #     header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
    #     # Comments sheet
    #     ws_comments = wb.active
    #     ws_comments.title = "Comments"
    #     ws_comments.append(['ID', 'Author', 'Email', 'Comment', 'Likes', 'Created At'])
    #     for cell in ws_comments[1]:
    #         cell.font = header_font
    #         cell.fill = header_fill
        
    #     comments = HubComment.objects.filter(content=content).select_related('author')
    #     for comment in comments:
    #         ws_comments.append([
    #             comment.id,
    #             comment.author.get_full_name() or comment.author.email,
    #             comment.author.email,
    #             comment.comment_text,
    #             comment.likes_count or 0,
    #             comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     # Likes sheet
    #     ws_likes = wb.create_sheet("Likes")
    #     ws_likes.append(['ID', 'User', 'Email', 'Created At'])
    #     for cell in ws_likes[1]:
    #         cell.font = header_font
    #         cell.fill = header_fill
        
    #     likes = ContentLike.objects.filter(content=content).select_related('user')
    #     for like in likes:
    #         ws_likes.append([
    #             like.id,
    #             like.user.get_full_name() or like.user.email,
    #             like.user.email,
    #             like.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     # Bookmarks sheet
    #     ws_bookmarks = wb.create_sheet("Bookmarks")
    #     ws_bookmarks.append(['ID', 'User', 'Email', 'Created At'])
    #     for cell in ws_bookmarks[1]:
    #         cell.font = header_font
    #         cell.fill = header_fill
        
    #     bookmarks = ContentBookmark.objects.filter(content=content).select_related('user')
    #     for bookmark in bookmarks:
    #         ws_bookmarks.append([
    #             bookmark.id,
    #             bookmark.user.get_full_name() or bookmark.user.email,
    #             bookmark.user.email,
    #             bookmark.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    #         ])
        
    #     # Adjust column widths for all sheets
    #     for ws in [ws_comments, ws_likes, ws_bookmarks]:
    #         for column in ws.columns:
    #             max_length = 0
    #             column_letter = column[0].column_letter
    #             for cell in column:
    #                 try:
    #                     if len(str(cell.value)) > max_length:
    #                         max_length = len(str(cell.value))
    #                 except:
    #                     pass
    #             adjusted_width = min(max_length + 2, 50)
    #             ws.column_dimensions[column_letter].width = adjusted_width
        
    #     # Save to response
    #     response = HttpResponse(
    #         content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     )
    #     response['Content-Disposition'] = f'attachment; filename="engagement_content_{content.id}_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    #     wb.save(response)
        
    #     return response



class AdminHubCommentViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing hub comments
    
    Features:
    - View all comments across hubs
    - Moderate comments (delete, approve)
    - Bulk actions
    - Filter by content, user, hub
    """
    queryset = HubComment.objects.all()
    serializer_class = HubCommentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['comment_text', 'author__email', 'author__first_name', 'author__last_name']
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter comments"""
        queryset = super().get_queryset().select_related(
            'author', 'content', 'parent_comment'
        ).prefetch_related('likes', 'replies')
        
        # Filter by hub type
        hub_type = self.request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Filter by content
        content_id = self.request.query_params.get('content_id')
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author_id')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'comment_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            },
            required=['comment_ids']
        ),
        responses={200: 'Comments deleted'}
    )
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete comments"""
        comment_ids = request.data.get('comment_ids', [])
        if not comment_ids:
            return Response({'error': 'No comment IDs provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = HubComment.objects.filter(id__in=comment_ids).delete()[0]
        return Response({
            'message': f'{deleted_count} comments deleted',
            'deleted_count': deleted_count
        })

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        responses={200: 'Statistics'}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comment statistics"""
        hub_type = request.query_params.get('hub_type')
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        stats = {
            'total_comments': queryset.count(),
            'recent_comments': queryset.filter(created_at__gte=start_date).count(),
            'top_level_comments': queryset.filter(parent_comment=None).count(),
            'replies': queryset.filter(parent_comment__isnull=False).count(),
            'by_hub_type': {},
        }
        
        # Hub type breakdown
        for ht in queryset.values('hub_type').annotate(count=Count('id')):
            stats['by_hub_type'][ht['hub_type']] = ht['count']
        
        return Response(stats)


class AdminHubUserActivityViewSet(viewsets.ViewSet):
    """
    Admin API for monitoring user activity across hubs
    
    Features:
    - View user engagement metrics
    - Track content creation
    - Monitor purchases and revenue
    - Identify top contributors
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        responses={200: 'User activity data'}
    )
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get detailed activity for a specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        hub_type = request.query_params.get('hub_type')
        
        # Content created
        content_qs = LearningMaterial.objects.filter(uploader_id=user_id)
        if hub_type:
            content_qs = content_qs.filter(hub_type=hub_type)
        
        # Engagement
        likes_given = ContentLike.objects.filter(user_id=user_id).count()
        comments_made = HubComment.objects.filter(author_id=user_id).count()
        bookmarks_made = ContentBookmark.objects.filter(user_id=user_id).count()
        
        # Students Hub specific
        purchases_made = LearningMaterialPurchase.objects.filter(user_id=user_id).count()
        purchases_received = LearningMaterialPurchase.objects.filter(
            material__uploader_id=user_id
        ).count()
        
        revenue_earned = LearningMaterialPurchase.objects.filter(
            material__uploader_id=user_id
        ).aggregate(total=Sum('material__price'))['total'] or 0
        
        followers_count = LecturerFollow.objects.filter(lecturer_id=user_id).count()
        following_count = LecturerFollow.objects.filter(student_id=user_id).count()
        
        return Response({
            'user_id': user_id,
            'content_created': content_qs.count(),
            'content_by_hub': {
                ht['hub_type']: ht['count'] 
                for ht in content_qs.values('hub_type').annotate(count=Count('id'))
            },
            'engagement': {
                'likes_given': likes_given,
                'comments_made': comments_made,
                'bookmarks_made': bookmarks_made,
            },
            'students_hub': {
                'purchases_made': purchases_made,
                'purchases_received': purchases_received,
                'revenue_earned': float(revenue_earned),
                'followers': followers_count,
                'following': following_count,
            },
            'total_views': content_qs.aggregate(total=Sum('views_count'))['total'] or 0,
            'total_downloads': content_qs.aggregate(total=Sum('downloads_count'))['total'] or 0,
        })

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('hub_type', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('metric', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                            description='content_count, views, downloads, revenue'),
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ],
        responses={200: 'Top contributors list'}
    )
    @action(detail=False, methods=['get'])
    def top_contributors(self, request):
        """Get top content contributors"""
        hub_type = request.query_params.get('hub_type')
        metric = request.query_params.get('metric', 'content_count')
        limit = int(request.query_params.get('limit', 10))
        
        queryset = LearningMaterial.objects.all()
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        if metric == 'content_count':
            top_users = queryset.values(
                'uploader__id', 'uploader__first_name', 'uploader__last_name', 'uploader__email'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
        elif metric == 'views':
            top_users = queryset.values(
                'uploader__id', 'uploader__first_name', 'uploader__last_name', 'uploader__email'
            ).annotate(
                total_views=Sum('views_count')
            ).order_by('-total_views')[:limit]
        elif metric == 'downloads':
            top_users = queryset.values(
                'uploader__id', 'uploader__first_name', 'uploader__last_name', 'uploader__email'
            ).annotate(
                total_downloads=Sum('downloads_count')
            ).order_by('-total_downloads')[:limit]
        elif metric == 'revenue':
            # Students Hub only
            purchases = LearningMaterialPurchase.objects.select_related('material__uploader')
            if hub_type:
                purchases = purchases.filter(material__hub_type=hub_type)
            
            top_users = purchases.values(
                'material__uploader__id',
                'material__uploader__first_name',
                'material__uploader__last_name',
                'material__uploader__email'
            ).annotate(
                total_revenue=Sum('material__price')
            ).order_by('-total_revenue')[:limit]
        else:
            top_users = []
        
        return Response(list(top_users))
