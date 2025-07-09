from rest_framework import serializers
from projects.models.sprint_model import Sprint
from projects.models.project_model import Project


class SprintSerializer(serializers.ModelSerializer):
    projects = serializers.PrimaryKeyRelatedField(many=True, queryset=Project.objects.all(), required=False)

    class Meta:
        model = Sprint
        fields = ['id', 'name', 'description', 'start_date', 'end_date', 'projects']