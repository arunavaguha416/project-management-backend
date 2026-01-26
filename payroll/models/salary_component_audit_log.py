
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

class SalaryComponentAuditLog(SoftDeletionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    component = models.ForeignKey(
        SalaryComponent,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )
    action = models.CharField(
        max_length=20,
        choices=[
            ("CREATED", "Created"),
            ("UPDATED", "Updated"),
            ("TOGGLED", "Toggled"),
        ]
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    snapshot = models.JSONField()  # full state after change
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('SalaryComponentAuditLog')
        verbose_name_plural = _('SalaryComponentAuditLogs')
