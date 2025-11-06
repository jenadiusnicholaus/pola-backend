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
        
        return queryset.select_related('asker', 'answered_by', 'material')
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def answer(self, request, pk=None):
        """Answer a question"""
        question = self.get_object()
        answer_text = request.data.get('answer_text')
        
        if not answer_text:
            return Response({'error': 'answer_text required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as answered
        question.mark_as_answered(answerer=request.user, answer_text=answer_text)
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)
    
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
