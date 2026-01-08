from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
from ..models.task_model import Task
import uuid


class SprintAISnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    sprint = models.ForeignKey(
        "Sprint",
        on_delete=models.CASCADE,
        related_name="ai_snapshots"
    )
    probability = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
