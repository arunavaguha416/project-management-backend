from rest_framework import serializers
from tasks.models.task_model import Task
from django.contrib.auth.models import User

class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'project', 'project_id',
            'assigned_to', 'assigned_to_id', 'created_at', 'updated_at'
        ]