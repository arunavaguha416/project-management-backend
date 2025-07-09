from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid

class TimeEntry(SoftDeletionModel):
    
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    duration = models.DurationField()  # e.g., '01:30:00' for 1 hour 30 minutes
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('TimeEntry')
        verbose_name_plural = _('TimeEntries')