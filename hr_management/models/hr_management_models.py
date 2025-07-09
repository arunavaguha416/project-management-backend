from django.db import models
from authentication.models.user import User
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from department.models.department_model import Department
from company.models.company_model import Company

class Employee(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    comp_id = models.ForeignKey(Company, on_delete=models.CASCADE, db_index=True,null=True)
    dept_id = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True,null=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employeies')

    

class LeaveRequest(SoftDeletionModel):
    STATUS_TYPES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, 
                        default=uuid.uuid4, 
                        editable=False, 
                        unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('LeaveRequest')
        verbose_name_plural = _('LeaveRequests')