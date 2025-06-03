from rest_framework import serializers
from notifications.models.notification_model import Notification

class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
         model = Notification
         fields = [
            'id', 'message', 'recipient', 'recipient_id', 'notification_type', 'is_read',
            'related_object', 'content_type', 'object_id', 'created_at', 'updated_at',
            'deleted_at', 'published_at'
         ]

        