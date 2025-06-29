# department/models.py
from django.db import models
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from authentication.models.user import User
from .depertment_model import Department

# Define the Department model to represent organizational units
class DepertmentUSerMapping(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    dept_id = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "DepertmentUSerMapping"
        verbose_name_plural = "DepertmentUSerMappings"