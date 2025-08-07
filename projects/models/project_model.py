from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from company.models.company_model import Company

class Project(SoftDeletionModel):
    class projectStatus(models.TextChoices):
        Ongoing='Ongoing'
        Completed='Completed'
        

    id = models.UUIDField(primary_key=True, 
                         default=uuid.uuid4, 
                         editable=False, 
                         unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects',null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects',null=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manager',null=True)
    resource = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='brought_projects')
    status = models.CharField(max_length=10, choices=projectStatus.choices, default=projectStatus.Ongoing, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')



