from rest_framework import serializers
from projects.models.comments_model import Comment


class CommentUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)


class CommentSerializer(serializers.ModelSerializer):   

    created_by = CommentUserSerializer(source='comment_by', read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'content', 'comment_by', 'task', 'created_at', 'updated_at','created_by',]
        