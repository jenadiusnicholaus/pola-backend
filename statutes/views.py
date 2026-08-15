from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import StatuteCategory, Statute
from .serializers import StatuteCategorySerializer, StatuteSerializer


class StatuteCategoryViewSet(viewsets.ModelViewSet):
    """
    Public (authenticated): list/retrieve active categories.
    Admin: full CRUD with soft delete.
    """
    serializer_class = StatuteCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'name_sw', 'description', 'description_sw']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = StatuteCategory.all_objects.annotate(
            statutes_count=Count(
                'statutes',
                filter=Q(statutes__is_active=True, statutes__deleted_at__isnull=True),
            )
        )
        if self.request.user.is_staff:
            include_deleted = self.request.query_params.get('include_deleted') == 'true'
            if not include_deleted and self.action in ('list',):
                # Admin list: by default show non-deleted (active + inactive soft-hidden)
                show_deleted = self.request.query_params.get('show_deleted') == 'true'
                if show_deleted:
                    return qs.filter(deleted_at__isnull=False)
                return qs.filter(deleted_at__isnull=True)
            return qs
        return qs.filter(is_active=True, deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restore(self, request, pk=None):
        category = self.get_object()
        category.restore()
        return Response(self.get_serializer(category).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_active(self, request, pk=None):
        category = self.get_object()
        if category.deleted_at:
            return Response(
                {'error': 'Category is deleted. Restore it first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category.is_active = not category.is_active
        category.save(update_fields=['is_active', 'updated_at'])
        return Response(self.get_serializer(category).data)


class StatuteViewSet(viewsets.ModelViewSet):
    """
    Public (authenticated): list/retrieve active statutes (filter by category).
    Admin: full CRUD + PDF upload, soft delete.
    """
    serializer_class = StatuteSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'categories']
    search_fields = ['title', 'title_sw', 'description', 'description_sw']
    ordering_fields = ['sort_order', 'title', 'created_at']
    ordering = ['sort_order', 'title']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = Statute.all_objects.prefetch_related('categories')
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(categories__id=category_id)

        if self.request.user.is_staff:
            show_deleted = self.request.query_params.get('show_deleted') == 'true'
            if self.action == 'list':
                if show_deleted:
                    return qs.filter(deleted_at__isnull=False).distinct()
                return qs.filter(deleted_at__isnull=True).distinct()
            return qs.distinct()

        return qs.filter(is_active=True, deleted_at__isnull=True).distinct()

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restore(self, request, pk=None):
        statute = self.get_object()
        statute.restore()
        return Response(self.get_serializer(statute).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_active(self, request, pk=None):
        statute = self.get_object()
        if statute.deleted_at:
            return Response(
                {'error': 'Statute is deleted. Restore it first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        statute.is_active = not statute.is_active
        statute.save(update_fields=['is_active', 'updated_at'])
        return Response(self.get_serializer(statute).data)
