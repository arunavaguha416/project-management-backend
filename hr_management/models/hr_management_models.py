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
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_index=True,null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True,null=True)
    salary = models.CharField(max_length=100, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=15, blank=True)
    tax_regime = models.CharField(max_length=10,choices=[('OLD', 'Old'), ('NEW', 'New')],default='NEW')
    # salary_structure = models.ForeignKey(SalaryStructure,on_delete=models.SET_NULL,null=True, blank=True)

    is_payroll_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employeies')

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    in_time = models.TimeField(null=True, blank=True)
    out_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        unique_together = ('employee', 'date')
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'


class LeaveBalance(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    balance = models.IntegerField(default=24)


class LeaveRequest(SoftDeletionModel):
    STATUS_TYPES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default='PENDING')
    
    # Enhanced tracking fields
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    comments = models.TextField(blank=True, help_text="Approver's comments")
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('LeaveRequest')
        verbose_name_plural = _('LeaveRequests')
