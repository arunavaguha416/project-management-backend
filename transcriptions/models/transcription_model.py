from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

from authentication.models.user import User
from project_management.softDeleteModel import SoftDeletionModel


class Transcription(SoftDeletionModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('QUEUED', 'Queued'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to='transcriptions/', null=True, blank=True)
    meeting_id = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    summary = models.JSONField(null=True, blank=True)
    created_by =  models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('transcription')
        verbose_name_plural = _('transcriptions')
