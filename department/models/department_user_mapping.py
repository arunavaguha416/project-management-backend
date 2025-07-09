# department/models.py
from django.db import models
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from authentication.models.user import User
from .department_model import Department

# Define the Department model to represent organizational units
class DepartmentUSerMapping(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "DepartmentUSerMapping"
        verbose_name_plural = "DepartmentUSerMappings"