from django.db import models
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
import uuid

class Sprint(SoftDeletionModel):
    STATUS_CHOICES = [  # 🆕 New field
        ('PLANNED', 'Planned'),
        ('ACTIVE', 'Active'),  
        ('COMPLETED', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # 🔄 Changed from ManyToMany to ForeignKey for simpler structure
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints',null=True,blank=True)  # ✅ Allow null temporarily
          # ✅ Allow blank in forms)
    
    # 🆕 Enhanced fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    goal = models.TextField(null=True, blank=True)
    velocity = models.IntegerField(default=0, help_text="Sprint velocity in story points")
    ai_completion_probability = models.IntegerField(default=0, help_text="AI predicted completion %")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Sprint')
        verbose_name_plural = _('Sprints')
