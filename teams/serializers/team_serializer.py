from rest_framework import serializers
from teams.models.team_model import Team

class TeamSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = Team
        fields = [
            'id', 'name', 'description', 'members', 'member_ids', 'projects', 'project_ids',
            'created_at', 'updated_at', 'deleted_at', 'published_at'
        ]

        