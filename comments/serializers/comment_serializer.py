from rest_framework import serializers
from comments.models.comment_model import Comment

class CommentSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_id', 'project', 'project_id', 'task', 'task_id',
            'parent', 'created_at', 'updated_at', 'deleted_at', 'published_at'
        ]