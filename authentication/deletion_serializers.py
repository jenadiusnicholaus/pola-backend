from rest_framework import serializers
from .models import AccountDeletionRequest


class AccountDeletionRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    data_category_labels = serializers.SerializerMethodField()

    class Meta:
        model = AccountDeletionRequest
        fields = [
            'id', 'user', 'user_email', 'user_name', 'deletion_type',
            'data_categories', 'data_category_labels', 'reason', 'status',
            'admin_notes', 'processed_by', 'processed_at',
            'scheduled_deletion_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'admin_notes', 'processed_by',
            'processed_at', 'scheduled_deletion_date', 'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        name = obj.user.get_full_name()
        return name if name else obj.user.email

    def get_data_category_labels(self, obj):
        labels = dict(AccountDeletionRequest.DATA_CATEGORIES)
        return [labels.get(cat, cat) for cat in (obj.data_categories or [])]


class CreateAccountDeletionSerializer(serializers.Serializer):
    """Serializer for requesting account or data deletion."""
    deletion_type = serializers.ChoiceField(
        choices=AccountDeletionRequest.DELETION_TYPES, default='account'
    )
    data_categories = serializers.ListField(
        child=serializers.ChoiceField(choices=AccountDeletionRequest.DATA_CATEGORIES),
        required=False, default=list
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    confirm = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs.get('deletion_type') == 'account':
            if not attrs.get('confirm'):
                raise serializers.ValidationError({
                    'confirm': 'You must set confirm=true to request account deletion.'
                })
        if attrs.get('deletion_type') == 'data':
            if not attrs.get('data_categories'):
                raise serializers.ValidationError({
                    'data_categories': 'Specify at least one data category to delete.'
                })
        return attrs
