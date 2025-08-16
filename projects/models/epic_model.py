from django.db import models
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
import uuid


class Epic(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)

    # Basic fields
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(blank=True, null=True)

    # Project association
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='epics',
        null=True,
        blank=True
    )

    # UI/label color (hex)
    color = models.CharField(
        max_length=7,
        default='#36B37E',
        help_text="Epic identification color"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    # SoftDeletionModel already includes deleted_at; add updated_at if you need it frequently
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Epic')
        verbose_name_plural = _('Epics')
