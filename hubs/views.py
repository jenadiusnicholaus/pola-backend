"""
Hub Views - Educational Content Organization
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Count, Prefetch

from .models import LegalEdTopic, LegalEdSubTopic
from .serializers import (
    TopicListSerializer, TopicDetailSerializer,
    SubtopicListSerializer, SubtopicDetailSerializer
)
from documents.models import LearningMaterial


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Topics
    
    Endpoints:
    - GET /topics/ - List all topics
    - GET /topics/{id}/ - Get topic details with subtopics
    - GET /topics/{id}/subtopics/ - Get all subtopics in a topic
    """
    queryset = LegalEdTopic.objects.filter(is_active=True).prefetch_related('subtopics')
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TopicDetailSerializer
        return TopicListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(name_sw__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('display_order', 'name')
    
    @action(detail=True, methods=['get'])
    def subtopics(self, request, slug=None):
        """Get all subtopics in a topic"""
        topic = self.get_object()
        subtopics = topic.subtopics.filter(is_active=True)

        # Language filter
        language = request.query_params.get('language')
        if language in ('en', 'sw'):
            subtopics = subtopics.filter(language=language)

        subtopics = subtopics.order_by('display_order', 'name')

        serializer = SubtopicListSerializer(subtopics, many=True, context={'request': request})
        return Response({
            'topic_id': topic.id,
            'topic_name': topic.name,
            'topic_name_sw': topic.name_sw,
            'subtopics_count': subtopics.count(),
            'subtopics': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def materials(self, request, slug=None):
        """Get all materials in a topic"""
        topic = self.get_object()
        
        # Get all materials: direct topic materials + subtopic materials
        from documents.models import LearningMaterial
        from django.db.models import Q
        
        materials = LearningMaterial.objects.filter(
            Q(topic=topic) |  # Direct topic materials (NEW)
            Q(subtopic__topic=topic, subtopic__is_active=True),  # Subtopic materials (legacy)
            is_active=True,
            is_approved=True
        ).select_related('uploader', 'subtopic', 'topic').order_by('-created_at')
        
        # Language filter
        language = request.query_params.get('language')
        if language:
            materials = materials.filter(language=language)
        
        # Basic search if provided
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            materials = materials.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Pagination
        page = self.paginate_queryset(materials)
        if page is not None:
            from subscriptions.serializers import LearningMaterialSerializer
            serializer = LearningMaterialSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response({
                'topic_id': topic.id,
                'topic_name': topic.name,
                'topic_name_sw': topic.name_sw,
                'materials_count': materials.count(),
                'materials': serializer.data
            })
        
        # No pagination
        from subscriptions.serializers import LearningMaterialSerializer
        serializer = LearningMaterialSerializer(materials, many=True, context={'request': request})
        
        return Response({
            'topic_id': topic.id,
            'topic_name': topic.name,
            'topic_name_sw': topic.name_sw,
            'materials_count': materials.count(),
            'materials': serializer.data
        })


class SubtopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Subtopics
    
    Endpoints:
    - GET /subtopics/ - List all subtopics
    - GET /subtopics/{id}/ - Get subtopic details
    - GET /subtopics/{id}/materials/ - Get all materials in a subtopic
    
    Note: Free trial users are limited to viewing 5 subtopics.
    """
    queryset = LegalEdSubTopic.objects.filter(is_active=True).select_related('topic')
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubtopicDetailSerializer
        return SubtopicListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get subtopic details.
        For free trial users, tracks and limits subtopic access.
        """
        from subscriptions.permissions import check_legal_education_access
        
        instance = self.get_object()
        
        # Check if user can access this subtopic (Free trial limit)
        if not request.user.is_staff and not request.user.is_superuser:
            can_access, error_response = check_legal_education_access(request.user, instance.id)
            if not can_access:
                return Response(error_response, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by topic - support both ?topic=1 and ?topic_id=1 and ?topic_slug=xxx
        topic_id = self.request.query_params.get('topic') or self.request.query_params.get('topic_id')
        topic_slug = self.request.query_params.get('topic_slug')

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        elif topic_slug:
            queryset = queryset.filter(topic__slug=topic_slug)

        # Filter by language only on list action - not on detail/materials (would break get_object)
        if self.action == 'list':
            language = self.request.query_params.get('language')
            if language in ('en', 'sw'):
                queryset = queryset.filter(language=language)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_sw__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('topic__display_order', 'display_order', 'name')
    
    @action(detail=True, methods=['get'])
    def materials(self, request, slug=None):
        """
        Get all materials in a subtopic.
        For free trial users, tracks and limits subtopic access.
        """
        from subscriptions.permissions import check_legal_education_access
        from rest_framework.pagination import PageNumberPagination

        subtopic = self.get_object()
        language = request.query_params.get('language')

        # Check if user can access this subtopic (Free trial limit)
        if not request.user.is_staff and not request.user.is_superuser:
            can_access, error_response = check_legal_education_access(request.user, subtopic.id)
            if not can_access:
                return Response(error_response, status=status.HTTP_403_FORBIDDEN)

        # Get materials with basic filtering
        materials = LearningMaterial.objects.filter(
            subtopic=subtopic,
            is_active=True,
            is_approved=True
        ).select_related('uploader').order_by('-created_at')

        # Language filter
        if language in ('en', 'sw'):
            materials = materials.filter(language=language)

        # Basic search if provided
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            materials = materials.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        page = paginator.paginate_queryset(materials, request)

        # Language-specific names for response metadata
        subtopic_name = subtopic.name_sw if language == 'sw' and subtopic.name_sw else subtopic.name
        topic_name = subtopic.topic.name_sw if language == 'sw' and subtopic.topic.name_sw else subtopic.topic.name

        # Import serializer here to avoid circular import
        from subscriptions.serializers import LearningMaterialSerializer

        if page is not None:
            serializer = LearningMaterialSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response({
                'subtopic_id': subtopic.id,
                'subtopic_name': subtopic_name,
                'topic_id': subtopic.topic.id,
                'topic_name': topic_name,
                'language': language or subtopic.language,
                'materials_count': materials.count(),
            })

        # Fallback if pagination is disabled
        serializer = LearningMaterialSerializer(materials, many=True, context={'request': request})
        return Response({
            'subtopic_id': subtopic.id,
            'subtopic_name': subtopic_name,
            'topic_id': subtopic.topic.id,
            'topic_name': topic_name,
            'language': language or subtopic.language,
            'materials_count': materials.count(),
            'materials': serializer.data
        })
