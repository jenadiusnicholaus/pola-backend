"""
Admin Views for Hubs Management
Comprehensive admin API for managing topics, subtopics, and educational content
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Q, Avg
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import LegalEdTopic, LegalEdSubTopic
from documents.models import LearningMaterial
from .admin_serializers import (
    TopicAdminListSerializer,
    TopicAdminDetailSerializer,
    TopicAdminCreateUpdateSerializer,
    SubtopicAdminListSerializer,
    SubtopicAdminDetailSerializer,
    SubtopicAdminCreateUpdateSerializer,
    ReorderSerializer,
    BulkToggleSerializer,
    TopicStatsSerializer,
    SubtopicStatsSerializer
)


class TopicAdminViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing Legal Education Topics
    
    Provides complete CRUD operations, reordering, bulk actions, and statistics for topics.
    All endpoints require admin authentication.
    
    Endpoints:
    - GET    /admin/hubs/topics/                   - List all topics
    - POST   /admin/hubs/topics/                   - Create new topic
    - GET    /admin/hubs/topics/{id}/              - Get topic details
    - PUT    /admin/hubs/topics/{id}/              - Update topic
    - PATCH  /admin/hubs/topics/{id}/              - Partial update topic
    - DELETE /admin/hubs/topics/{id}/              - Delete topic
    - POST   /admin/hubs/topics/{id}/toggle/       - Toggle active status
    - POST   /admin/hubs/topics/reorder/           - Reorder topics
    - POST   /admin/hubs/topics/bulk-toggle/       - Bulk toggle active
    - GET    /admin/hubs/topics/stats/             - Get statistics
    """
    queryset = LegalEdTopic.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return TopicAdminDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TopicAdminCreateUpdateSerializer
        return TopicAdminListSerializer
    
    def get_queryset(self):
        """Filter and search topics"""
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by name or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_sw__icontains=search) |
                Q(description__icontains=search) |
                Q(description_sw__icontains=search)
            )
        
        # Filter topics without subtopics
        no_subtopics = self.request.query_params.get('no_subtopics')
        if no_subtopics == 'true':
            queryset = queryset.annotate(
                subtopics_count=Count('subtopics')
            ).filter(subtopics_count=0)
        
        # Filter topics without materials
        no_materials = self.request.query_params.get('no_materials')
        if no_materials == 'true':
            # Get topics that have no materials in any subtopic
            topics_with_materials = LearningMaterial.objects.values_list(
                'subtopic__topic', flat=True
            ).distinct()
            queryset = queryset.exclude(id__in=topics_with_materials)
        
        return queryset.prefetch_related('subtopics').order_by('display_order', 'name')
    
    def perform_destroy(self, instance):
        """Check if topic can be deleted"""
        subtopics_count = instance.subtopics.count()
        if subtopics_count > 0:
            raise serializers.ValidationError(
                f"Cannot delete topic with {subtopics_count} subtopics. "
                "Delete subtopics first."
            )
        instance.delete()
    
    @swagger_auto_schema(
        operation_description="Toggle topic active status. Deactivating a topic also deactivates all subtopics.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Target active status (optional, toggles if not provided)')
            }
        ),
        responses={200: TopicAdminDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle topic active status"""
        topic = self.get_object()
        is_active = request.data.get('is_active')
        
        if is_active is None:
            is_active = not topic.is_active
        
        topic.is_active = is_active
        topic.save()
        
        # Also update all subtopics if deactivating
        if not is_active:
            affected_subtopics = topic.subtopics.filter(is_active=True).count()
            topic.subtopics.update(is_active=False)
            message = f"Topic deactivated. {affected_subtopics} subtopics also deactivated."
        else:
            message = "Topic activated."
        
        serializer = TopicAdminDetailSerializer(topic)
        return Response({
            'success': True,
            'message': message,
            'topic': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Reorder topics by updating display_order for multiple topics at once",
        request_body=ReorderSerializer,
        responses={200: 'Successfully reordered topics'}
    )
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder topics by updating display_order
        
        Request body:
        {
            "items": [
                {"id": 1, "display_order": 0},
                {"id": 2, "display_order": 1},
                {"id": 3, "display_order": 2}
            ]
        }
        """
        serializer = ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        items = serializer.validated_data['items']
        
        with transaction.atomic():
            for item in items:
                LegalEdTopic.objects.filter(id=item['id']).update(
                    display_order=item['display_order']
                )
        
        return Response({
            'success': True,
            'message': f"Successfully reordered {len(items)} topics",
            'items': items
        })
    
    @swagger_auto_schema(
        operation_description="Bulk toggle active status for multiple topics. Deactivating topics also deactivates all subtopics.",
        request_body=BulkToggleSerializer,
        responses={200: 'Successfully updated topics'}
    )
    @action(detail=False, methods=['post'])
    def bulk_toggle(self, request):
        """
        Bulk toggle active status for multiple topics
        
        Request body:
        {
            "ids": [1, 2, 3],
            "is_active": true
        }
        """
        serializer = BulkToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ids = serializer.validated_data['ids']
        is_active = serializer.validated_data['is_active']
        
        # Update topics
        updated_count = LegalEdTopic.objects.filter(id__in=ids).update(is_active=is_active)
        
        # If deactivating, also deactivate all subtopics
        if not is_active:
            affected_subtopics = LegalEdSubTopic.objects.filter(
                topic_id__in=ids
            ).update(is_active=False)
        else:
            affected_subtopics = 0
        
        return Response({
            'success': True,
            'message': f"Updated {updated_count} topics",
            'updated_count': updated_count,
            'affected_subtopics': affected_subtopics,
            'is_active': is_active
        })
    
    @swagger_auto_schema(
        operation_description="Quick create topic by name for content creation",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Topic name'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Topic description (optional)')
            },
            required=['name']
        ),
        responses={201: TopicAdminDetailSerializer, 200: TopicAdminDetailSerializer}
    )
    @action(detail=False, methods=['post'])
    def quick_create(self, request):
        """Create topic by name if it doesn't exist, return existing if it does"""
        name = request.data.get('name', '').strip()
        description = request.data.get('description', '').strip()
        
        if not name:
            return Response({'error': 'Topic name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if topic already exists (case-insensitive)
        existing_topic = LegalEdTopic.objects.filter(name__iexact=name).first()
        if existing_topic:
            serializer = TopicAdminDetailSerializer(existing_topic)
            return Response({
                'topic': serializer.data,
                'created': False,
                'message': f'Topic "{name}" already exists'
            }, status=status.HTTP_200_OK)
        
        # Create new topic
        from django.utils.text import slugify
        new_topic_data = {
            'name': name,
            'slug': slugify(name),
            'description': description or f'Auto-created topic: {name}',
            'display_order': LegalEdTopic.objects.count() + 1,
            'is_active': True
        }
        
        serializer = TopicAdminCreateUpdateSerializer(data=new_topic_data)
        if serializer.is_valid():
            topic = serializer.save()
            detail_serializer = TopicAdminDetailSerializer(topic)
            return Response({
                'topic': detail_serializer.data,
                'created': True,
                'message': f'Topic "{name}" created successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get comprehensive statistics about topics, subtopics, and materials",
        responses={200: TopicStatsSerializer}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get topic statistics"""
        total_topics = LegalEdTopic.objects.count()
        active_topics = LegalEdTopic.objects.filter(is_active=True).count()
        inactive_topics = total_topics - active_topics
        
        total_subtopics = LegalEdSubTopic.objects.count()
        total_materials = LearningMaterial.objects.count()
        
        # Topics without subtopics
        topics_without_subtopics = LegalEdTopic.objects.annotate(
            subtopics_count=Count('subtopics')
        ).filter(subtopics_count=0).count()
        
        # Topics without materials
        topics_with_materials = LearningMaterial.objects.values_list(
            'subtopic__topic', flat=True
        ).distinct()
        topics_without_materials = total_topics - len(set(topics_with_materials))
        
        stats = {
            'total_topics': total_topics,
            'active_topics': active_topics,
            'inactive_topics': inactive_topics,
            'total_subtopics': total_subtopics,
            'total_materials': total_materials,
            'topics_without_subtopics': topics_without_subtopics,
            'topics_without_materials': topics_without_materials
        }
        
        serializer = TopicStatsSerializer(stats)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Get all materials in this topic (both direct and from subtopics)",
        manual_parameters=[
            openapi.Parameter('is_approved', openapi.IN_QUERY, description="Filter by approval status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('include_subtopic_materials', openapi.IN_QUERY, description="Include materials from subtopics", type=openapi.TYPE_BOOLEAN, default=True),
            openapi.Parameter('content_type', openapi.IN_QUERY, description="Filter by content type", type=openapi.TYPE_STRING),
            openapi.Parameter('uploader_type', openapi.IN_QUERY, description="Filter by uploader type", type=openapi.TYPE_STRING),
            openapi.Parameter('language', openapi.IN_QUERY, description="Filter by language (en/sw)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in title and description", type=openapi.TYPE_STRING),
        ],
        responses={200: 'List of materials in topic'}
    )
    @action(detail=True, methods=['get'])
    def materials(self, request, pk=None):
        """Get all materials in this topic (NEW: Direct topic-to-materials + subtopic materials)"""
        topic = self.get_object()
        
        # Get parameters
        include_subtopic_materials = request.query_params.get('include_subtopic_materials', 'true').lower() == 'true'
        is_approved = request.query_params.get('is_approved')
        is_active = request.query_params.get('is_active')
        content_type = request.query_params.get('content_type')
        uploader_type = request.query_params.get('uploader_type')
        language = request.query_params.get('language')
        search = request.query_params.get('search')
        
        # Get direct materials (NEW feature)
        direct_materials = LearningMaterial.objects.filter(topic=topic).select_related('uploader')
        
        # Get subtopic materials (backward compatibility)
        subtopic_materials = LearningMaterial.objects.filter(
            subtopic__topic=topic
        ).select_related('uploader', 'subtopic')
        
        # Combine querysets based on preference
        if include_subtopic_materials:
            materials = direct_materials.union(subtopic_materials)
        else:
            materials = direct_materials
        
        # Apply filters
        if is_approved is not None:
            materials = materials.filter(is_approved=is_approved.lower() == 'true')
        
        if is_active is not None:
            materials = materials.filter(is_active=is_active.lower() == 'true')
        
        if content_type:
            materials = materials.filter(content_type=content_type)
        
        if uploader_type:
            materials = materials.filter(uploader_type=uploader_type)
        
        if language and language in ['en', 'sw']:
            materials = materials.filter(language=language)
        
        if search:
            materials = materials.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Order materials
        materials = materials.order_by('-created_at')
        
        # Import serializer to avoid circular import
        from subscriptions.admin_document_serializers import LearningMaterialAdminSerializer
        serializer = LearningMaterialAdminSerializer(materials, many=True)
        
        # Get counts for response
        direct_count = direct_materials.count()
        subtopic_count = subtopic_materials.count()
        
        return Response({
            'topic_id': topic.id,
            'topic_name': topic.name,
            'topic_name_sw': topic.name_sw,
            'materials_count': materials.count(),
            'direct_materials_count': direct_count,
            'subtopic_materials_count': subtopic_count,
            'include_subtopic_materials': include_subtopic_materials,
            'applied_filters': {
                'is_approved': is_approved,
                'is_active': is_active,
                'content_type': content_type,
                'uploader_type': uploader_type,
                'language': language,
                'search': search,
            },
            'materials': serializer.data
        })


class SubtopicAdminViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing Legal Education Subtopics
    
    Provides complete CRUD operations, reordering, bulk actions, statistics, and material management for subtopics.
    All endpoints require admin authentication.
    
    Endpoints:
    - GET    /admin/hubs/subtopics/                - List all subtopics
    - POST   /admin/hubs/subtopics/                - Create new subtopic
    - GET    /admin/hubs/subtopics/{id}/           - Get subtopic details
    - PUT    /admin/hubs/subtopics/{id}/           - Update subtopic
    - PATCH  /admin/hubs/subtopics/{id}/           - Partial update subtopic
    - DELETE /admin/hubs/subtopics/{id}/           - Delete subtopic
    - POST   /admin/hubs/subtopics/{id}/toggle/    - Toggle active status
    - POST   /admin/hubs/subtopics/reorder/        - Reorder subtopics
    - POST   /admin/hubs/subtopics/bulk-toggle/    - Bulk toggle active
    - GET    /admin/hubs/subtopics/stats/          - Get statistics
    - GET    /admin/hubs/subtopics/{id}/materials/ - Get materials in subtopic
    """
    queryset = LegalEdSubTopic.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return SubtopicAdminDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubtopicAdminCreateUpdateSerializer
        return SubtopicAdminListSerializer
    
    def get_queryset(self):
        """Filter and search subtopics"""
        queryset = super().get_queryset()
        
        # Filter by topic
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by name or description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_sw__icontains=search) |
                Q(description__icontains=search) |
                Q(description_sw__icontains=search) |
                Q(topic__name__icontains=search)
            )
        
        # Filter subtopics without materials
        no_materials = self.request.query_params.get('no_materials')
        if no_materials == 'true':
            subtopics_with_materials = LearningMaterial.objects.values_list(
                'subtopic', flat=True
            ).distinct()
            queryset = queryset.exclude(id__in=subtopics_with_materials)
        
        return queryset.select_related('topic').order_by(
            'topic__display_order', 'display_order', 'name'
        )
    
    def perform_destroy(self, instance):
        """Check if subtopic can be deleted"""
        materials_count = LearningMaterial.objects.filter(subtopic=instance).count()
        if materials_count > 0:
            raise serializers.ValidationError(
                f"Cannot delete subtopic with {materials_count} materials. "
                "Delete or reassign materials first."
            )
        instance.delete()
    
    @swagger_auto_schema(
        operation_description="Toggle subtopic active status",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Target active status (optional, toggles if not provided)')
            }
        ),
        responses={200: SubtopicAdminDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle subtopic active status"""
        subtopic = self.get_object()
        is_active = request.data.get('is_active')
        
        if is_active is None:
            is_active = not subtopic.is_active
        
        subtopic.is_active = is_active
        subtopic.save()
        
        serializer = SubtopicAdminDetailSerializer(subtopic)
        return Response({
            'success': True,
            'message': f"Subtopic {'activated' if is_active else 'deactivated'}",
            'subtopic': serializer.data
        })
    
    @swagger_auto_schema(
        operation_description="Reorder subtopics by updating display_order for multiple subtopics at once",
        request_body=ReorderSerializer,
        responses={200: 'Successfully reordered subtopics'}
    )
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder subtopics by updating display_order
        
        Request body:
        {
            "items": [
                {"id": 1, "display_order": 0},
                {"id": 2, "display_order": 1},
                {"id": 3, "display_order": 2}
            ]
        }
        """
        serializer = ReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        items = serializer.validated_data['items']
        
        with transaction.atomic():
            for item in items:
                LegalEdSubTopic.objects.filter(id=item['id']).update(
                    display_order=item['display_order']
                )
        
        return Response({
            'success': True,
            'message': f"Successfully reordered {len(items)} subtopics",
            'items': items
        })
    
    @swagger_auto_schema(
        operation_description="Bulk toggle active status for multiple subtopics",
        request_body=BulkToggleSerializer,
        responses={200: 'Successfully updated subtopics'}
    )
    @action(detail=False, methods=['post'])
    def bulk_toggle(self, request):
        """
        Bulk toggle active status for multiple subtopics
        
        Request body:
        {
            "ids": [1, 2, 3],
            "is_active": true
        }
        """
        serializer = BulkToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ids = serializer.validated_data['ids']
        is_active = serializer.validated_data['is_active']
        
        updated_count = LegalEdSubTopic.objects.filter(id__in=ids).update(is_active=is_active)
        
        return Response({
            'success': True,
            'message': f"Updated {updated_count} subtopics",
            'updated_count': updated_count,
            'is_active': is_active
        })
    
    @swagger_auto_schema(
        operation_description="Get comprehensive statistics about subtopics and materials",
        responses={200: SubtopicStatsSerializer}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subtopic statistics"""
        total_subtopics = LegalEdSubTopic.objects.count()
        active_subtopics = LegalEdSubTopic.objects.filter(is_active=True).count()
        inactive_subtopics = total_subtopics - active_subtopics
        
        total_materials = LearningMaterial.objects.count()
        
        # Subtopics without materials
        subtopics_with_materials = LearningMaterial.objects.values_list(
            'subtopic', flat=True
        ).distinct()
        subtopics_without_materials = total_subtopics - len(set(subtopics_with_materials))
        
        # Average materials per subtopic
        materials_per_subtopic = LearningMaterial.objects.values('subtopic').annotate(
            count=Count('id')
        ).aggregate(avg=Avg('count'))
        
        avg_materials = materials_per_subtopic['avg'] or 0.0
        
        stats = {
            'total_subtopics': total_subtopics,
            'active_subtopics': active_subtopics,
            'inactive_subtopics': inactive_subtopics,
            'total_materials': total_materials,
            'subtopics_without_materials': subtopics_without_materials,
            'avg_materials_per_subtopic': round(avg_materials, 2)
        }
        
        serializer = SubtopicStatsSerializer(stats)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Get all materials under this subtopic with optional filtering",
        manual_parameters=[
            openapi.Parameter('is_approved', openapi.IN_QUERY, description="Filter by approval status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
        ],
        responses={200: 'List of materials in subtopic'}
    )
    @action(detail=True, methods=['get'])
    def materials(self, request, pk=None):
        """Get all materials in this subtopic"""
        subtopic = self.get_object()
        
        materials = LearningMaterial.objects.filter(subtopic=subtopic).select_related(
            'uploader'
        ).order_by('-created_at')
        
        # Filter by status
        is_approved = request.query_params.get('is_approved')
        if is_approved is not None:
            materials = materials.filter(is_approved=is_approved.lower() == 'true')
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            materials = materials.filter(is_active=is_active.lower() == 'true')
        
        # Import serializer to avoid circular import
        from subscriptions.admin_document_serializers import LearningMaterialAdminSerializer
        serializer = LearningMaterialAdminSerializer(materials, many=True)
        
        return Response({
            'subtopic_id': subtopic.id,
            'subtopic_name': subtopic.name,
            'topic_name': subtopic.topic.name,
            'materials_count': materials.count(),
            'materials': serializer.data
        })
