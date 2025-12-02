"""
Unified Hub Views - Single API for all hubs (Advocates, Students, Forum)
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from documents.models import (
    LearningMaterial, LearningMaterialPurchase,
    LecturerFollow, MaterialQuestion, MaterialRating
)
from .models import HubComment, ContentLike, ContentBookmark, HubCommentLike, HubMessage
from .serializers import (
    HubContentSerializer, HubContentCreateSerializer, HubCommentSerializer, ContentLikeSerializer,
    ContentBookmarkSerializer, LecturerFollowSerializer,
    MaterialQuestionSerializer, MaterialRatingSerializer, HubMessageSerializer
)
from .permissions import (
    CanAccessHub, IsOwnerOrReadOnly, CanCreateContent,
    CanPurchaseContent, CanFollowLecturer
)


class HubContentViewSet(viewsets.ModelViewSet):
    """
    Unified ViewSet for ALL hub content (posts + documents)
    
    Works for: Advocates Hub, Students Hub, Community Forum, Legal Education
    
    Query params:
    - hub_type: advocates|students|forum|legal_ed
    - content_type: discussion|question|article|news|document|notes|past_papers|etc
    - uploader_type: student|lecturer|advocate|admin
    - search: search in title, description, content
    - ordering: -created_at (default), -views_count, -likes_count, price, etc
    """
    queryset = LearningMaterial.objects.filter(is_active=True, is_approved=True)
    serializer_class = HubContentSerializer
    permission_classes = [CanAccessHub, CanCreateContent | IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['hub_type', 'content_type', 'uploader_type', 'is_pinned', 'is_lecture_material']
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['created_at', 'views_count', 'downloads_count', 'price', 'is_pinned']
    ordering = ['-created_at']  # Latest content first, regardless of pinned status
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action in ['create', 'update', 'partial_update']:
            return HubContentCreateSerializer
        return HubContentSerializer
    
    def get_queryset(self):
        """Filter queryset based on permissions and query params"""
        queryset = super().get_queryset()
        
        # Filter by hub_type from query params
        hub_type = self.request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Show only pinned
        pinned_only = self.request.query_params.get('pinned_only')
        if pinned_only == 'true':
            queryset = queryset.filter(is_pinned=True)
        
        return queryset.select_related('uploader').prefetch_related('likes', 'comments', 'bookmarks')
    
    def perform_create(self, serializer):
        """Set uploader to current user"""
        serializer.save(uploader=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Increment views when retrieving content"""
        instance = self.get_object()
        
        # Increment view count
        LearningMaterial.objects.filter(pk=instance.pk).update(
            views_count=instance.views_count + 1
        )
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like content"""
        content = self.get_object()
        like, created = ContentLike.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        if created:
            return Response({'message': 'Content liked'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already liked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Unlike content"""
        content = self.get_object()
        deleted_count, _ = ContentLike.objects.filter(
            user=request.user,
            content=content
        ).delete()
        
        if deleted_count > 0:
            return Response({'message': 'Content unliked'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Not liked'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def bookmark(self, request, pk=None):
        """Bookmark content"""
        content = self.get_object()
        bookmark, created = ContentBookmark.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        if created:
            return Response({'message': 'Content bookmarked'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already bookmarked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def unbookmark(self, request, pk=None):
        """Remove bookmark"""
        content = self.get_object()
        deleted_count, _ = ContentBookmark.objects.filter(
            user=request.user,
            content=content
        ).delete()
        
        if deleted_count > 0:
            return Response({'message': 'Bookmark removed'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Not bookmarked'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def bookmarked(self, request):
        """Get all bookmarked content for the authenticated user"""
        from documents.models import LearningMaterial
        
        # Get bookmarked content IDs for this user
        bookmarked_content_ids = ContentBookmark.objects.filter(
            user=request.user
        ).values_list('content_id', flat=True)
        
        # Get the actual content with filtering support
        queryset = LearningMaterial.objects.filter(
            id__in=bookmarked_content_ids,
            is_active=True,
            is_approved=True
        ).select_related('uploader').prefetch_related('likes', 'comments', 'bookmarks')
        
        # Apply manual filters using the same logic as main viewset
        hub_type = request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        content_type = request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        is_downloadable = request.query_params.get('is_downloadable')
        if is_downloadable is not None:
            is_downloadable_bool = is_downloadable.lower() in ['true', '1']
            queryset = queryset.filter(is_downloadable=is_downloadable_bool)
        
        # Apply search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(content__icontains=search)
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HubContentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = HubContentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def liked(self, request):
        """Get all liked content for the authenticated user"""
        from documents.models import LearningMaterial
        
        # Get liked content IDs for this user
        liked_content_ids = ContentLike.objects.filter(
            user=request.user
        ).values_list('content_id', flat=True)
        
        # Get the actual content with filtering support
        queryset = LearningMaterial.objects.filter(
            id__in=liked_content_ids,
            is_active=True,
            is_approved=True
        ).select_related('uploader').prefetch_related('likes', 'comments', 'bookmarks')
        
        # Apply manual filters (same as bookmarked)
        hub_type = request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        content_type = request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        is_downloadable = request.query_params.get('is_downloadable')
        if is_downloadable is not None:
            is_downloadable_bool = is_downloadable.lower() in ['true', '1']
            queryset = queryset.filter(is_downloadable=is_downloadable_bool)
        
        # Apply search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(content__icontains=search)
            )
        
        # Apply ordering
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HubContentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = HubContentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending content based on engagement (views, likes, comments)"""
        from documents.models import LearningMaterial
        from datetime import datetime, timedelta
        
        # Get content from the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        queryset = LearningMaterial.objects.filter(
            is_active=True,
            is_approved=True,
            created_at__gte=thirty_days_ago
        ).select_related('uploader').prefetch_related('likes', 'comments', 'bookmarks')
        
        # Apply hub type filter
        hub_type = request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Calculate trending score: (views * 0.1) + (likes * 2) + (comments * 3) + (bookmarks * 1.5)
        from django.db.models import F, FloatField
        from django.db.models.functions import Cast
        
        queryset = queryset.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True), 
            bookmarks_count=Count('bookmarks', distinct=True),
            trending_score=(
                Cast(F('views_count'), FloatField()) * 0.1 +
                Cast(Count('likes', distinct=True), FloatField()) * 2.0 +
                Cast(Count('comments', distinct=True), FloatField()) * 3.0 +
                Cast(Count('bookmarks', distinct=True), FloatField()) * 1.5
            )
        ).order_by('-trending_score', '-created_at')
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HubContentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = HubContentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get most recent content"""
        from documents.models import LearningMaterial
        
        queryset = LearningMaterial.objects.filter(
            is_active=True,
            is_approved=True
        ).select_related('uploader').prefetch_related('likes', 'comments', 'bookmarks')
        
        # Apply hub type filter
        hub_type = request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        # Apply content type filter  
        content_type = request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Order by most recent first
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HubContentSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = HubContentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for this content"""
        content = self.get_object()
        comments = HubComment.objects.filter(
            content=content,
            parent_comment=None,  # Top-level only
            is_active=True
        ).select_related('author').prefetch_related('replies')
        
        serializer = HubCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[])
    def view(self, request, pk=None):
        """Track content view - increment view count"""
        try:
            content = self.get_object()
            
            # Increment view count
            content.views_count += 1
            content.save(update_fields=['views_count'])
            
            return Response({
                'message': 'View tracked successfully',
                'views_count': content.views_count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # If content not accessible, still return success to avoid breaking frontend
            return Response({
                'message': 'View tracking skipped',
                'views_count': 0
            }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get content analytics and statistics"""
        content = self.get_object()
        
        # Calculate engagement rate (likes + bookmarks + comments) / views
        total_engagement = (
            content.likes.count() + 
            content.bookmarks.count() + 
            content.comments.count()
        )
        engagement_rate = total_engagement / max(content.views_count, 1)
        
        # Get average rating
        average_rating = content.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        
        analytics_data = {
            'views_count': content.views_count,
            'downloads_count': content.downloads_count,
            'likes_count': content.likes.count(),
            'bookmarks_count': content.bookmarks.count(),
            'comments_count': content.comments.count(),
            'ratings_count': content.ratings.count(),
            'average_rating': round(average_rating, 2),
            'engagement_rate': round(engagement_rate, 3),
            'purchase_count': content.purchases.count() if hasattr(content, 'purchases') else 0,
        }
        
        return Response(analytics_data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPurchaseContent])
    def purchase(self, request, pk=None):
        """Purchase content (Students Hub only)"""
        content = self.get_object()
        
        # Check if already purchased
        if LearningMaterialPurchase.objects.filter(buyer=request.user, material=content).exists():
            return Response(
                {'message': 'Already purchased'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record purchase and calculate revenue split
        result = content.record_purchase(buyer=request.user)
        
        return Response({
            'message': 'Purchase successful',
            'purchase_id': result['purchase'].id,
            'uploader_share': float(result['uploader_share']),
            'platform_share': float(result['app_share'])
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get', 'post'])
    def questions(self, request, pk=None):
        """Get or ask questions about this material"""
        content = self.get_object()
        
        if request.method == 'GET':
            questions = MaterialQuestion.objects.filter(material=content).select_related('asker', 'answered_by')
            serializer = MaterialQuestionSerializer(questions, many=True, context={'request': request})
            return Response(serializer.data)
        
        # POST - ask a question
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = MaterialQuestionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(material=content, asker=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        """Rate content (Students Hub)"""
        content = self.get_object()
        
        # Check if already rated
        existing_rating = MaterialRating.objects.filter(material=content, rater=request.user).first()
        
        if existing_rating:
            # Update existing rating
            serializer = MaterialRatingSerializer(existing_rating, data=request.data, partial=True, context={'request': request})
        else:
            # Create new rating
            serializer = MaterialRatingSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(material=content, rater=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED if not existing_rating else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HubCommentViewSet(viewsets.ModelViewSet):
    """
    Unified ViewSet for comments across all hubs
    """
    queryset = HubComment.objects.filter(is_active=True)
    serializer_class = HubCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter comments based on hub_type and content_id"""
        queryset = super().get_queryset()
        
        hub_type = self.request.query_params.get('hub_type')
        if hub_type:
            queryset = queryset.filter(hub_type=hub_type)
        
        content_id = self.request.query_params.get('content_id')
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        
        return queryset.select_related('author', 'content').prefetch_related('replies')
    
    def perform_create(self, serializer):
        """Set author to current user and ensure hub_type matches content"""
        # Get the content being commented on
        content = serializer.validated_data.get('content')
        hub_type = content.hub_type if content else None
        
        serializer.save(
            author=self.request.user,
            hub_type=hub_type
        )
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a comment"""
        comment = self.get_object()
        like, created = HubCommentLike.objects.get_or_create(
            user=request.user,
            comment=comment
        )
        
        if created:
            return Response({'message': 'Comment liked'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Already liked'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        """Unlike a comment"""
        comment = self.get_object()
        deleted_count, _ = HubCommentLike.objects.filter(
            user=request.user,
            comment=comment
        ).delete()
        
        if deleted_count > 0:
            return Response({'message': 'Comment unliked'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Not liked'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies to this comment"""
        comment = self.get_object()
        replies = comment.replies.filter(is_active=True).select_related('author')
        
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)


class LecturerFollowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for following lecturers (Students Hub)
    """
    queryset = LecturerFollow.objects.filter(is_active=True)
    serializer_class = LecturerFollowSerializer
    permission_classes = [IsAuthenticated, CanFollowLecturer]
    
    def get_queryset(self):
        """Get user's followed lecturers"""
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        
        return self.queryset.filter(student=self.request.user).select_related('lecturer')
    
    @action(detail=False, methods=['post'])
    def follow(self, request):
        """Follow a lecturer"""
        lecturer_id = request.data.get('lecturer_id')
        
        if not lecturer_id:
            return Response({'error': 'lecturer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get lecturer user
        from authentication.models import PolaUser
        lecturer = get_object_or_404(PolaUser, id=lecturer_id, user_role='lecturer')
        
        # Create or update follow
        follow, created = LecturerFollow.objects.get_or_create(
            student=request.user,
            lecturer=lecturer,
            defaults={'is_active': True, 'notifications_enabled': True}
        )
        
        if not created and not follow.is_active:
            follow.is_active = True
            follow.save()
        
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def unfollow(self, request):
        """Unfollow a lecturer"""
        lecturer_id = request.data.get('lecturer_id')
        
        if not lecturer_id:
            return Response({'error': 'lecturer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count, _ = LecturerFollow.objects.filter(
            student=request.user,
            lecturer_id=lecturer_id
        ).delete()
        
        if deleted_count > 0:
            return Response({'message': 'Unfollowed'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Not following this lecturer'}, status=status.HTTP_404_NOT_FOUND)


class MaterialQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Q&A on materials (Students Hub)
    """
    queryset = MaterialQuestion.objects.all()
    serializer_class = MaterialQuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'helpful_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter questions"""
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by material
        material_id = self.request.query_params.get('material_id')
        if material_id:
            queryset = queryset.filter(material_id=material_id)
        
        # Filter by asker
        asker_id = self.request.query_params.get('asker_id')
        if asker_id:
            queryset = queryset.filter(asker_id=asker_id)
        
        return queryset.select_related('asker', 'answered_by', 'material')
    
    def perform_create(self, serializer):
        """Set asker to current user when creating a question"""
        serializer.save(asker=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_helpful(self, request, pk=None):
        """Mark question/answer as helpful"""
        question = self.get_object()
        question.helpful_count += 1
        question.save()
        
        return Response({'message': 'Marked as helpful', 'helpful_count': question.helpful_count})


class HubMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for private messages
    """
    queryset = HubMessage.objects.all()
    serializer_class = HubMessageSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get user's messages"""
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()
        
        return self.queryset.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).select_related('sender', 'recipient')
    
    def perform_create(self, serializer):
        """Set sender to current user"""
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get received messages"""
        messages = self.get_queryset().filter(recipient=request.user)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get sent messages"""
        messages = self.get_queryset().filter(sender=request.user)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        
        # Only recipient can mark as read
        if message.recipient != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if not message.is_read:
            from django.utils import timezone
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
        
        return Response({'message': 'Marked as read'})
