from django.db import models
from hr_management.models.hr_management_models import Employee
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from company.models.company_model import Company

class Project(SoftDeletionModel):
    class projectStatus(models.TextChoices):
        PLANNING = 'Planning'
        ONGOING = 'Ongoing' 
        COMPLETED = 'Completed'
        ON_HOLD = 'On Hold'
        CANCELLED = 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200,null=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='manager', null=True)
    status = models.CharField(max_length=20, choices=projectStatus.choices, default=projectStatus.PLANNING, null=True, blank=True, db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # 🆕 Enhanced fields
    color_scheme = models.CharField(max_length=7, default='#0060DF', help_text="Hex color for project theming")
    ai_health_score = models.IntegerField(default=0, help_text="AI-calculated project health (0-100)")
    priority = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')
    ], default='MEDIUM')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')


class UserMapping(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_to')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "UserMapping"
        verbose_name_plural = "UserMappings"


class ManagerMapping(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
   
    manager = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='project_manager')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "ManagerMapping"
        verbose_name_plural = "ManagerMappings"


class Milestone(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    name = models.CharField(max_length=200, blank=True)  # Alternative field name
    description = models.TextField(blank=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='milestones')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    target_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)  # Alternative field name
    completion_percentage = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#FF5630', help_text="Milestone color indicator")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"






