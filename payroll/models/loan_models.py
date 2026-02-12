from django.db import models
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
from hr_management.models.hr_management_models import Employee
import uuid


class LoanAdvance(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loan_advances')
    loan_type = models.CharField(
        max_length=20,
        choices=[
            ('Loan', 'Loan'),
            ('Advance', 'Advance'),
        ],
        default='Loan'
    )
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    emi_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tenure_months = models.PositiveIntegerField(default=12)
    disbursed_date = models.DateField()
    next_deduction_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Active', 'Active'),
            ('Closed', 'Closed'),
            ('Paused', 'Paused'),
        ],
        default='Active'
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('LoanAdvance')
        verbose_name_plural = _('LoanAdvances')
        ordering = ['-created_at']
