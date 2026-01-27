from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from projects.models.project_model import Project
import uuid
from projects.models.sprint_model import Sprint
from projects.models.epic_model import Epic
class Task(SoftDeletionModel):
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'), 
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),  # 🆕 Added
    )

    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),  # 🆕 Added
        ('DONE', 'Done'),
        ('BLOCKED', 'Blocked'),  # 🆕 Added
    )
    
    TYPE_CHOICES = (  # 🆕 New field
        ('STORY', 'Story'),
        ('BUG', 'Bug'),
        ('TASK', 'Task'),
        ('SUBTASK', 'Subtask'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')  # Fixed default
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')  # Fixed default
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TASK')  # 🆕 New
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Ordering of task within sprint/status column"
    )
    # 🆕 Enhanced fields
    epic = models.ForeignKey(Epic, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    story_points = models.IntegerField(null=True, blank=True)
    labels = models.JSONField(default=list, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    time_estimate = models.DurationField(null=True, blank=True)
    time_logged = models.DurationField(null=True, blank=True, default='00:00:00')
    progress_percentage = models.IntegerField(default=0)
    ai_suggested_assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_suggested_tasks')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

class TaskStatusHistory(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    from_status = models.CharField(max_length=50)
    to_status = models.CharField(max_length=50)
    changed_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
