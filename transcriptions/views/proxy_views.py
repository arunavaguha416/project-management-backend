import os
import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from transcriptions.models.transcription_model import Transcription


TRANSCRIPTION_BASE_URL = os.getenv("TRANSCRIPTION_BASE_URL", "http://127.0.0.1:8001")
TIMEOUT = float(os.getenv("TRANSCRIPTION_TIMEOUT", "20"))


def _auth_headers(request):
    auth = request.headers.get("Authorization")
    if not auth:
        return {}
    return {"Authorization": auth}


class TranscriptionUploadProxy(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        title = request.data.get("title")
        audio_file = request.FILES.get("audio_file")

        if not title or not audio_file:
            return Response(
                {"status": False, "message": "title and audio_file are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        record = Transcription.objects.create(
            title=title,
            audio_file=audio_file,
            created_by=request.user,
            status="PENDING"
        )

        try:
            resp = requests.post(
                f"{TRANSCRIPTION_BASE_URL}/api/meetings/upload/",
                data={"title": title},
                files={"audio_file": audio_file},
                headers=_auth_headers(request),
                timeout=TIMEOUT
            )
            data = resp.json()
            if resp.status_code in [200, 201] and data.get("data", {}).get("id"):
                record.meeting_id = str(data["data"]["id"])
                record.status = "QUEUED"
                record.save(update_fields=["meeting_id", "status"])
            return Response(data, status=resp.status_code)
        except Exception as e:
            record.status = "FAILED"
            record.save(update_fields=["status"])
            return Response(
                {"status": False, "message": f"Transcription service error: {e}"},
                status=status.HTTP_502_BAD_GATEWAY
            )


class TranscriptionTriggerProxy(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        meeting_id = request.data.get("meeting_id")
        if not meeting_id:
            return Response(
                {"status": False, "message": "meeting_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resp = requests.post(
                f"{TRANSCRIPTION_BASE_URL}/api/transcriptions/trigger/",
                json={"meeting_id": meeting_id},
                headers=_auth_headers(request),
                timeout=TIMEOUT
            )
            Transcription.objects.filter(meeting_id=meeting_id).update(status="PROCESSING")
            return Response(resp.json(), status=resp.status_code)
        except Exception as e:
            return Response(
                {"status": False, "message": f"Transcription service error: {e}"},
                status=status.HTTP_502_BAD_GATEWAY
            )


class TranscriptionStatusProxy(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        meeting_id = request.data.get("meeting_id")
        if not meeting_id:
            return Response(
                {"status": False, "message": "meeting_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resp = requests.post(
                f"{TRANSCRIPTION_BASE_URL}/api/transcriptions/status/",
                json={"meeting_id": meeting_id},
                headers=_auth_headers(request),
                timeout=TIMEOUT
            )
            data = resp.json()
            st = data.get("transcription_status")
            if st:
                Transcription.objects.filter(meeting_id=meeting_id).update(status=st)
            return Response(resp.json(), status=resp.status_code)
        except Exception as e:
            return Response(
                {"status": False, "message": f"Transcription service error: {e}"},
                status=status.HTTP_502_BAD_GATEWAY
            )


class TranscriptionResultProxy(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        meeting_id = request.data.get("meeting_id")
        if not meeting_id:
            return Response(
                {"status": False, "message": "meeting_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resp = requests.post(
                f"{TRANSCRIPTION_BASE_URL}/api/transcriptions/result/",
                json={"meeting_id": meeting_id},
                headers=_auth_headers(request),
                timeout=TIMEOUT
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("summary") is not None:
                Transcription.objects.filter(meeting_id=meeting_id).update(
                    status="COMPLETED",
                    summary=data.get("summary")
                )
            return Response(resp.json(), status=resp.status_code)
        except Exception as e:
            return Response(
                {"status": False, "message": f"Transcription service error: {e}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
