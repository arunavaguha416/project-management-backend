from rest_framework import serializers
from projects.models.task_model import Task



class TaskSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'project_id', 'assigned_to']
        