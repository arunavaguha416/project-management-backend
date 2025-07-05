from rest_framework import serializers
from projects.models.comments_model import Comment



class CommentSerializer(serializers.ModelSerializer):   
    class Meta:
        model = Comment
        fields = ['id', 'content', 'comment_by', 'task', 'created_at', 'updated_at']
        