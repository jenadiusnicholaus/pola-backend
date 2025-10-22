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
    queryset = LegalEdTopic.objects.filter(is_active=True).select_related('hub').prefetch_related('subtopics')
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
        subtopics = topic.subtopics.filter(is_active=True).order_by('display_order', 'name')
        
        serializer = SubtopicListSerializer(subtopics, many=True)
        return Response({
            'topic_id': topic.id,
            'topic_name': topic.name,
            'topic_name_sw': topic.name_sw,
            'subtopics_count': subtopics.count(),
            'subtopics': serializer.data
        })


class SubtopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Subtopics
    
    Endpoints:
    - GET /subtopics/ - List all subtopics
    - GET /subtopics/{id}/ - Get subtopic details
    - GET /subtopics/{id}/materials/ - Get all materials in a subtopic
    """
    queryset = LegalEdSubTopic.objects.filter(is_active=True).select_related('topic', 'topic__hub')
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubtopicDetailSerializer
        return SubtopicListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by topic
        topic_id = self.request.query_params.get('topic_id', None)
        topic_slug = self.request.query_params.get('topic_slug', None)
        
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        elif topic_slug:
            queryset = queryset.filter(topic__slug=topic_slug)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(name_sw__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('topic__display_order', 'display_order', 'name')
    
    @action(detail=True, methods=['get'])
    def materials(self, request, slug=None):
        """Get all materials in a subtopic"""
        subtopic = self.get_object()
        
        # Get language preference
        language = request.query_params.get('language', 'en')
        
        # Get materials
        materials = LearningMaterial.objects.filter(
            subtopic=subtopic,
            is_active=True,
            is_approved=True
        ).select_related('uploader')
        
        # Filter by language if specified
        if language in ['en', 'sw']:
            materials = materials.filter(language=language)
        
        # Import serializer here to avoid circular import
        from subscriptions.serializers import LearningMaterialSerializer
        serializer = LearningMaterialSerializer(materials, many=True)
        
        return Response({
            'subtopic_id': subtopic.id,
            'subtopic_name': subtopic.name,
            'subtopic_name_sw': subtopic.name_sw,
            'topic_name': subtopic.topic.name,
            'language': language,
            'materials_count': materials.count(),
            'materials': serializer.data
        })
