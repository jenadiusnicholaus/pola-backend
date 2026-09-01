from rest_framework import serializers
from .models import BlockedUser, UserReport


class BlockedUserSerializer(serializers.ModelSerializer):
    blocked_email = serializers.CharField(source='blocked.email', read_only=True)
    blocked_name = serializers.SerializerMethodField()
    blocked_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = BlockedUser
        fields = [
            'id', 'blocker', 'blocked', 'blocked_email', 'blocked_name',
            'blocked_profile_picture', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'blocker', 'created_at']

    def get_blocked_name(self, obj):
        name = obj.blocked.get_full_name()
        return name if name else obj.blocked.email

    def get_blocked_profile_picture(self, obj):
        if obj.blocked.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.blocked.profile_picture.url)
            return obj.blocked.profile_picture.url
        return None


class BlockUserSerializer(serializers.Serializer):
    """Serializer for blocking a user."""
    user_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class UserReportSerializer(serializers.ModelSerializer):
    reporter_email = serializers.CharField(source='reporter.email', read_only=True)
    reported_user_email = serializers.CharField(source='reported_user.email', read_only=True)
    reported_user_name = serializers.SerializerMethodField()

    class Meta:
        model = UserReport
        fields = [
            'id', 'reporter', 'reporter_email', 'reported_user', 'reported_user_email',
            'reported_user_name', 'report_type', 'description', 'content_type',
            'content_id', 'status', 'admin_notes', 'resolved_by', 'resolved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reporter', 'status', 'admin_notes', 'resolved_by',
            'resolved_at', 'created_at', 'updated_at'
        ]

    def get_reported_user_name(self, obj):
        if obj.reported_user:
            name = obj.reported_user.get_full_name()
            return name if name else obj.reported_user.email
        return None


class CreateReportSerializer(serializers.Serializer):
    """Serializer for creating a report."""
    reported_user_id = serializers.IntegerField(required=False)
    report_type = serializers.ChoiceField(choices=UserReport.REPORT_TYPES, default='other')
    description = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    content_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
