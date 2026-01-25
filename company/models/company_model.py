# department/models.py
from django.db import models
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from authentication.models.user import User

# Define the Department model to represent organizational units
class Company(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True, null=True)
    pan = models.CharField(max_length=100, unique=True, null=True)
    tan = models.CharField(max_length=100, unique=True, null=True)
    description = models.TextField(blank=True,null=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

class UserMapping(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "UserMapping"
        verbose_name_plural = "UserMappings"