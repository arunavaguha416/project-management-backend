from django.db import models
from django.utils.translation import gettext_lazy as _
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from decimal import Decimal
from datetime import date


class SalaryComponent(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50)
    component_type = models.CharField(
        max_length=10,
        choices=[('EARNING', 'Earning'), ('DEDUCTION', 'Deduction')]
    )
    calculation_type = models.CharField(
        max_length=15,
        choices=[('FIXED', 'Fixed'), ('PERCENTAGE', 'Percentage')]
    )
    percentage_of = models.CharField(
        max_length=10,
        choices=[('BASIC', 'Basic'), ('GROSS', 'Gross')],
        null=True, blank=True
    )
    is_taxable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('salary_component')
        verbose_name_plural = _('salary_components')

