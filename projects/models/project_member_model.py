
from django.db import models
from authentication.models.user import User
from projects.models.project_model import Project
import uuid

class ProjectMember(models.Model):

    ROLE_CHOICES = (
        ('OWNER', 'Owner'),
        ('MANAGER', 'Manager'),
        ('MEMBER', 'Member'),
        ('VIEWER', 'Viewer'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')

    is_active = models.BooleanField(default=True)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'
