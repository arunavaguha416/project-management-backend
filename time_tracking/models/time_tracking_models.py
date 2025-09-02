from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from datetime import date

class TimeEntry(SoftDeletionModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    login_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)  # Calculated field
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('TimeEntry')
        verbose_name_plural = _('TimeEntries')
        unique_together = ('user', 'date')  # One entry per user per day
    
    def calculate_duration(self):
        """Calculate duration between login and logout times"""
        if self.login_time and self.logout_time:
            self.duration = self.logout_time - self.login_time
        return self.duration
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration before saving
        self.calculate_duration()
        super().save(*args, **kwargs)
    
 
