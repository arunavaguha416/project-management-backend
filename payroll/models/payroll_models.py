# payroll/models/payroll_models.py

from django.db import models
from authentication.models.user import User
from hr_management.models.hr_management_models import Employee
from time_tracking.models.time_tracking_models import TimeEntry
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from decimal import Decimal
from datetime import date

class PayrollPeriod(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    period_name = models.CharField(max_length=100)  # e.g., "January 2024"
    status = models.CharField(max_length=20, choices=[
        ('Draft', 'Draft'),
        ('Processing', 'Processing'),
        ('Approved', 'Approved'),
        ('Paid', 'Paid')
    ], default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('PayrollPeriod')
        verbose_name_plural = _('PayrollPeriods')

class Payroll(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)

    # Salary Components
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Allowances
    house_rent_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Bonuses
    performance_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    attendance_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    project_bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Deductions
    provident_fund = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    health_insurance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Calculated Fields - These will be populated manually or via external services
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status and Processing
    status = models.CharField(max_length=20, choices=[
        ('Draft', 'Draft'),
        ('Calculated', 'Calculated'),
        ('Approved', 'Approved'),
        ('Paid', 'Paid')
    ], default='Draft')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Payroll')
        verbose_name_plural = _('Payrolls')
        unique_together = ('employee', 'payroll_period')

    # REMOVED: calculate_payroll method
    # REMOVED: custom save method that called calculate_payroll

class PerformanceMetric(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)

    # Performance Metrics
    project_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # %
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # out of 100
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # %
    client_feedback_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # out of 10
    team_collaboration_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # out of 10
    innovation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # out of 10

    # Overall Performance - These will be populated manually or via external services
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # calculated
    performance_grade = models.CharField(max_length=2, choices=[
        ('A+', 'Exceptional'),
        ('A', 'Outstanding'),
        ('B+', 'Above Average'),
        ('B', 'Average'),
        ('C', 'Below Average'),
        ('D', 'Poor')
    ], blank=True)
    bonus_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('PerformanceMetric')
        verbose_name_plural = _('PerformanceMetrics')
        unique_together = ('employee', 'period')

    # REMOVED: calculate_overall_score method
    # REMOVED: custom save method that called calculate_overall_score
