from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project

import uuid

class Discussion(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='discussions')
    participants = models.ManyToManyField(User, related_name='discussion_participants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Discussion')
        verbose_name_plural = _('Discussions')