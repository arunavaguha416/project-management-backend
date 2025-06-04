from rest_framework import serializers
from attachments.models.attachment_model import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
         model = Attachment
         fields = [
            'id', 'file', 'file_url', 'filename', 'uploader', 'uploader_id', 'related_object',
            'content_type', 'object_id', 'created_at', 'updated_at', 'deleted_at', 'published_at'
        ]

        