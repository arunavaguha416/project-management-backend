# department/models.py
from django.db import models
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from authentication.models.user import User

# Define the Department model to represent organizational units
class Department(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    name = models.CharField(max_length=100, unique=True,)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"