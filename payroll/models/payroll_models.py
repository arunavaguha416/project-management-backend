# payroll/models/payroll_models.py

from django.db import models
from authentication.models.user import User
from hr_management.models.hr_management_models import Employee
from payroll.models.salary_component import SalaryComponent
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
    financial_year = models.CharField(max_length=100,null=True, blank=True)
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


class PayRun(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('IN_PROGRESS', 'In Progress'),
        ('FINALIZED', 'Finalized'),
        ('POSTED', 'Posted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    payroll_period = models.OneToOneField(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='pay_run'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payruns_created'
    )

    finalized_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payruns_finalized'
    )

    finalized_at = models.DateTimeField(null=True, blank=True)

    total_employees = models.PositiveIntegerField(default=0)
    total_gross_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_net_salary = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=255, null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('payrun')
        
class Payroll(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    pay_run = models.ForeignKey(PayRun, on_delete=models.CASCADE, null=True, blank=True)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, null=True, blank=True)

    # Earnings
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    house_rent_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Deductions
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Totals
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Overtime
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    performance_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    project_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Attendence
    working_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    paid_leave_days = models.IntegerField(default=0)
    payable_days = models.IntegerField(default=0)
    lop_days = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[('CALCULATED', 'Calculated'), ('APPROVED', 'Approved')],
        default='CALCULATED'
    )

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

class PayrollComponent(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('payroll_component')
        verbose_name_plural = _('payroll_components')


# ===============================
# PAYROLL AUDIT TRAIL
# ===============================

class PayrollAuditLog(models.Model):
    payroll = models.ForeignKey(
        "Payroll",
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.field_name} changed for Payroll {self.payroll_id}"


# ===============================
# PAYROLL ROLLBACK AUDIT
# ===============================

class PayrollRollbackLog(models.Model):
    pay_run = models.ForeignKey(
        "PayRun",
        on_delete=models.CASCADE,
        related_name="rollback_logs"
    )
    rolled_back_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reason = models.TextField()
    rolled_back_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rollback for PayRun {self.pay_run_id}"
