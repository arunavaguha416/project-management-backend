from rest_framework import serializers
from projects.models.task_model import Task


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'task_type',
            'project_id',
            'assigned_to',
            'assigned_to_name',
            'assignee_name',
            'story_points',
            'due_date',
            'order',
            'labels',
            'progress_percentage'
        ]

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.name if obj.assigned_to else None

    def get_assignee_name(self, obj):
        return obj.assigned_to.name if obj.assigned_to else None
        
