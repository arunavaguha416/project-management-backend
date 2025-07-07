# department/models.py
from django.db import models
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from authentication.models.user import User
from .company_model import Company

# Define the Department model to represent organizational units
class CompanyUserMapping(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "CompanyUserMapping"
        verbose_name_plural = "CompanyUserMappings"