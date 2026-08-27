from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone

from .models import Event
from .serializers import EventSerializer


class EventAdminViewSet(viewsets.ModelViewSet):
    """
    Admin API for managing events.

    Endpoints:
    - GET /admin/events/ - List events
    - POST /admin/events/ - Create event
    - GET /admin/events/{id}/ - Retrieve event
    - PUT/PATCH /admin/events/{id}/ - Update event
    - DELETE /admin/events/{id}/ - Delete event
    - GET /admin/events/statistics/ - Event statistics
    """

    permission_classes = [IsAdminUser]
    serializer_class = EventSerializer
    queryset = Event.objects.all()
    lookup_field = "pk"

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Return counts by status."""
        total = Event.objects.count()
        published = Event.objects.filter(status="published").count()
        draft = Event.objects.filter(status="draft").count()
        cancelled = Event.objects.filter(status="cancelled").count()
        upcoming = Event.objects.filter(
            status="published", start_date__gte=timezone.now()
        ).count()
        return Response(
            {
                "total": total,
                "published": published,
                "draft": draft,
                "cancelled": cancelled,
                "upcoming": upcoming,
            }
        )
