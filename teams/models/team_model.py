from django.db import models
from authentication.models.user import User
from projects.models.project_model import Project
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid

class Team(SoftDeletionModel):
    
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    name = models.CharField(max_length=100)  
    project_id = models.ManyToManyField(Project, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')