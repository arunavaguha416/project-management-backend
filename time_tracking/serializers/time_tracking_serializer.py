from rest_framework import serializers
from time_tracking.models.time_tracking_models import TimeEntry

class TimeEntrySerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = TimeEntry
         
        fields = [
            'id', 'user', 'user_id', 'task', 'task_id', 'duration', 'date', 'description',
            'created_at', 'updated_at', 'deleted_at', 'published_at'
        ]

        