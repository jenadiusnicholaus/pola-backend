from notification.models import FcmNotification, UserNotification
from rest_framework import serializers


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notification history"""
    
    class Meta:
        model = UserNotification
        fields = [
            'id',
            'user',
            'notification_type',
            'title',
            'body',
            'data',
            'is_read',
            'read_at',
            'fcm_sent',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'fcm_sent', 'created_at', 'read_at']


class FcmNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FcmNotification
        fields = [
            'id',
            'user',
            'title',
            'body',
            'data',
            "to_user",
            'created_at',
            'updated_at'    
        ]
        read_only_fields = ('created_at', 'updated_at', 'id') 
        extra_kwargs = {
            'title': {'required': True},
            'body': {'required': True},
            'data': {'required': True},
            "to_user": {'required': True}
        }  

    def validate(self, data):
        # Custom validation logic
        if not data.get('title'):
            raise serializers.ValidationError({"title": "This field is required."})
        if not data.get('body'):
            raise serializers.ValidationError({"body": "This field is required."})
        if not data.get('data'):
            raise serializers.ValidationError({"data": "This field is required."})
        if not data.get('to_user'):
            raise serializers.ValidationError({"to_user": "This field is required."})
        
        # Return the validated data
        return data 



# NOTE: FcmTokenModelSerializer has been deprecated.
# FCM tokens are now managed via UserDevice model in authentication app.
# Use /api/v1/authentication/devices/register/ to register devices with FCM tokens
   