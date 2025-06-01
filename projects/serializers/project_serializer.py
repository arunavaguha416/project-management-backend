from rest_framework import serializers
from projects.models.project_model import Project

class ProjectSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = Project
        fields = ['id', 'user', 'name', 'description', 'created_at', 'updated_at', 'tasks']
        read_only_fields = ['user', 'created_at', 'updated_at', 'tasks']

        