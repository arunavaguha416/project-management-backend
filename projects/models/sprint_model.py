from django.db import models
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
import uuid


class Sprint(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                         default=uuid.uuid4, 
                         editable=False, 
                         unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    projects = models.ManyToManyField(Project, related_name='sprints', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Sprint')
        verbose_name_plural = _('Sprints')
