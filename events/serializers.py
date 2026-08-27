from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "location",
            "start_date",
            "end_date",
            "status",
            "is_featured",
            "cover_image_url",
            "max_attendees",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]
