from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from transcriptions.models.transcription_model import Transcription
from transcriptions.serializers.transcription_serializer import TranscriptionSerializer


class TranscriptionList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        records = Transcription.objects.filter(created_by=request.user).order_by('-created_at')
        serializer = TranscriptionSerializer(records, many=True)
        return Response({"status": True, "records": serializer.data}, status=status.HTTP_200_OK)


class TranscriptionDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        record_id = request.data.get('id')
        if not record_id:
            return Response({"status": False, "message": "id is required"}, status=status.HTTP_400_BAD_REQUEST)

        record = Transcription.objects.filter(id=record_id, created_by=request.user).first()
        if not record:
            return Response({"status": False, "message": "Record not found"}, status=status.HTTP_200_OK)

        serializer = TranscriptionSerializer(record)
        return Response({
            "status": True,
            "records": serializer.data
        }, status=status.HTTP_200_OK)
