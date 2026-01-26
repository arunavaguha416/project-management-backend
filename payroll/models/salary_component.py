from django.db import models
from django.utils.translation import gettext_lazy as _
from company.models.company_model import Company
from project_management.softDeleteModel import SoftDeletionModel
import uuid
from decimal import Decimal
from datetime import date


class SalaryComponent(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="salary_components",
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)

    component_type = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        choices=[("EARNING", "Earning"), ("DEDUCTION", "Deduction")]
    )

    calculation_type = models.CharField(
        max_length=15,
        blank=True,
        choices=[("FIXED", "Fixed"), ("PERCENTAGE", "Percentage")]
    )

    percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    percentage_of = models.CharField(
        max_length=10,
        choices=[("BASIC", "Basic"), ("GROSS", "Gross")],
        null=True,
        blank=True
    )

    is_taxable = models.BooleanField(default=True,null=True,
        blank=True)
    is_statutory = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True,null=True,
        blank=True)

    created_at = models.DateTimeField(auto_now_add=True,null=True,
        blank=True)

    class Meta:
        verbose_name = _('salary_component')
        verbose_name_plural = _('salary_components')

