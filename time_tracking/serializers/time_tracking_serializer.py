from rest_framework import serializers
from time_tracking.models.time_tracking_models import TimeEntry
from authentication.models.user import User

class TimeEntrySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    duration_hours = serializers.SerializerMethodField()
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = TimeEntry
        fields = [
            'id', 'user', 'user_name', 'user_email', 'date', 
            'login_time', 'logout_time', 'duration', 'duration_hours',
            'description', 'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'user', 'duration', 'created_at', 'updated_at']
    
    def get_duration_hours(self, obj):
        """Convert duration to readable hours format"""
        if obj.duration:
            total_seconds = obj.duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "0h 0m"

class UserTimeStatsSerializer(serializers.Serializer):
    total_days = serializers.IntegerField()
    total_hours = serializers.CharField()
    average_hours_per_day = serializers.CharField()
    current_week_hours = serializers.CharField()
    current_month_hours = serializers.CharField()
