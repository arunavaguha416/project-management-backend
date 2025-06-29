from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
import uuid

class Task(SoftDeletionModel):
    STATUS_CHOICES = [
        ('To Do'),
        ('In Progress'),
        ( 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('Low'),
        ('Medium'),
        ('High'),
    ]

    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To Do')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey( User, on_delete=models.SET_NULL, null=True, blank=True )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')