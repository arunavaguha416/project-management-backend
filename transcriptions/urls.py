from django.urls import path
from transcriptions.views.transcription_view import TranscriptionList, TranscriptionDetails
from transcriptions.views.proxy_views import (
    TranscriptionUploadProxy,
    TranscriptionTriggerProxy,
    TranscriptionStatusProxy,
    TranscriptionResultProxy,
)

urlpatterns = [
    path("upload/", TranscriptionUploadProxy.as_view()),
    path("trigger/", TranscriptionTriggerProxy.as_view()),
    path("status/", TranscriptionStatusProxy.as_view()),
    path("result/", TranscriptionResultProxy.as_view()),
    path("records/", TranscriptionList.as_view()),
    path("records/details/", TranscriptionDetails.as_view()),
]
