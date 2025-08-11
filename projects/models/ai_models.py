from django.db import models
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
from authentication.models.user import User
import uuid

class AIInsight(SoftDeletionModel):
    INSIGHT_TYPES = [
        ('SPRINT_HEALTH', 'Sprint Health'),
        ('WORKLOAD_BALANCE', 'Workload Balance'),
        ('BOTTLENECK_DETECTION', 'Bottleneck Detection'),
        ('VELOCITY_FORECAST', 'Velocity Forecast'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='ai_insights')
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200, null=True)
    description = models.TextField(blank=True, null=True)
    confidence_score = models.IntegerField(help_text="AI confidence (0-100)")
    data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UserPresence(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    current_view = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
