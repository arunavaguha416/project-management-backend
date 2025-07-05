from rest_framework import serializers
from projects.models.project_model import Project

class ProjectSerializer(serializers.ModelSerializer): 
    class Meta(object):
        model = Project
        fields = ['id', 'user', 'name', 'description', 'created_at', 'updated_at', 'tasks']
        

        