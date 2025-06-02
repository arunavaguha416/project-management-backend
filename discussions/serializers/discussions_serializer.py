from rest_framework import serializers
from discussions.models.discussions_model import Discussion

class CommentSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = Discussion
        fields = [
            'id', 'title', 'content', 'creator', 'creator_id', 'project', 'project_id',
            'participants', 'participant_ids', 'created_at', 'updated_at', 'deleted_at', 'published_at'
        ]