from rest_framework import serializers
from transcriptions.models.transcription_model import Transcription


class TranscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcription
        fields = [
            "id",
            "title",
            "audio_file",
            "meeting_id",
            "status",
            "summary",
            "created_by",
            "created_at",
            "updated_at",
        ]
