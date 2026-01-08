# projects/models/workflow_model.py

import uuid
from django.db import models
from projects.models.project_model import Project

class Workflow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='workflow')
    name = models.CharField(max_length=100, default='Default Workflow')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WorkflowStatus(models.Model):
    STATUS_TYPE_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),
        ('DONE', 'Done'),
        ('BLOCKED', 'Blocked'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='statuses')
    key = models.CharField(max_length=50)          # TODO, IN_PROGRESS
    label = models.CharField(max_length=100)       # "In Progress"
    order = models.PositiveIntegerField()
    is_terminal = models.BooleanField(default=False)

class WorkflowTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='transitions')

    from_status = models.ForeignKey(
        WorkflowStatus, on_delete=models.CASCADE, related_name='from_transitions'
    )
    to_status = models.ForeignKey(
        WorkflowStatus, on_delete=models.CASCADE, related_name='to_transitions'
    )

    allowed_roles = models.JSONField(default=list)  
    # ['OWNER', 'MANAGER', 'MEMBER']

    require_assignee = models.BooleanField(default=False)
    require_comment = models.BooleanField(default=False)

