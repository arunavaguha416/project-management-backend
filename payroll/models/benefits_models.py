# payroll/models/benefits_models.py
from django.db import models
from authentication.models.user import User
from hr_management.models.hr_management_models import Employee
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from decimal import Decimal
from datetime import date

class BenefitPlan(SoftDeletionModel):
    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    plan_type = models.CharField(max_length=50, choices=[
        ('Health Insurance', 'Health Insurance'),
        ('Life Insurance', 'Life Insurance'),
        ('Dental', 'Dental'),
        ('Vision', 'Vision'),
        ('Retirement', 'Retirement'),
        ('Flexible Spending', 'Flexible Spending'),
        ('Transportation', 'Transportation'),
        ('Other', 'Other')
    ])
    
    # Plan Details
    provider = models.CharField(max_length=200)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    employee_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Eligibility
    is_mandatory = models.BooleanField(default=False)
    eligibility_criteria = models.TextField(blank=True)
    waiting_period_days = models.IntegerField(default=0)
    
    # Enrollment
    enrollment_start_date = models.DateField()
    enrollment_end_date = models.DateField()
    plan_year_start = models.DateField()
    plan_year_end = models.DateField()
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('BenefitPlan')
        verbose_name_plural = _('BenefitPlans')

class BenefitEnrollment(SoftDeletionModel):
    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    benefit_plan = models.ForeignKey(BenefitPlan, on_delete=models.CASCADE)
    
    # Enrollment Details
    enrollment_date = models.DateField(default=date.today)
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Coverage Details
    coverage_level = models.CharField(max_length=50, choices=[
        ('Employee Only', 'Employee Only'),
        ('Employee + Spouse', 'Employee + Spouse'),
        ('Employee + Children', 'Employee + Children'),
        ('Family', 'Family')
    ], default='Employee Only')
    
    # Dependents
    spouse_covered = models.BooleanField(default=False)
    children_count = models.IntegerField(default=0)
    
    # Financial
    employee_monthly_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_monthly_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Terminated', 'Terminated')
    ], default='Pending')
    
    # Workflow
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_enrollments')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('BenefitEnrollment')
        verbose_name_plural = _('BenefitEnrollments')
        unique_together = ('employee', 'benefit_plan')

class TaxConfiguration(SoftDeletionModel):
    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    country = models.CharField(max_length=100, default='India')
    state = models.CharField(max_length=100, blank=True)
    
    # Tax Slabs
    tax_year = models.CharField(max_length=10)  # e.g., "2024-25"
    
    # Income Tax Slabs (JSON field or separate model)
    tax_slabs = models.JSONField(default=list)  # [{"min": 0, "max": 250000, "rate": 0}, ...]
    
    # Standard Deductions
    standard_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=50000)
    professional_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.5)  # %
    provident_fund_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.0)  # %
    
    # Other Taxes
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, default=4.0)  # Health and Education Cess %
    surcharge_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=5000000)
    surcharge_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # %
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('TaxConfiguration')
        verbose_name_plural = _('TaxConfigurations')
