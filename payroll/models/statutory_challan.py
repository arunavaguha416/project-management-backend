# payroll/models/statutory_challan.py
import uuid
from django.db import models
from project_management.softDeleteModel import SoftDeletionModel

class StatutoryChallan(SoftDeletionModel):
    STATUTORY_CHOICES = (
        ('PF', 'Provident Fund'),
        ('PT', 'Professional Tax'),
        ('TDS', 'Tax Deducted at Source'),
    )

    STATUS_CHOICES = (
        ('DUE', 'Due'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey('company.Company', on_delete=models.CASCADE)

    statutory_type = models.CharField(max_length=10, choices=STATUTORY_CHOICES)
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()

    challan_number = models.CharField(max_length=100, blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    receipt = models.FileField(upload_to='challans/', blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DUE')

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('company', 'statutory_type', 'month', 'year')

