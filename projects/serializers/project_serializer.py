from rest_framework import serializers
from projects.models.project_model import Project
from authentication.serializers.serializer import UserSerializer

class ProjectSerializer(serializers.ModelSerializer): 
    manager = UserSerializer(read_only=True)
    class Meta(object):
        model = Project
        fields = ['id', 'name', 'manager_id','manager','status']
        

        