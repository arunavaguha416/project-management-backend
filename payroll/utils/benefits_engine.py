from decimal import Decimal
from django.utils.timezone import now
from payroll.models.benefits_models import BenefitEnrollment


def calculate_benefit_deductions(employee):
    """
    Calculates employee-side benefit deductions
    for currently active enrollments.
    """

    today = now().date()

    enrollments = BenefitEnrollment.objects.filter(
        employee=employee,
        status="ACTIVE",                # ✅ correct field
        effective_date__lte=today,      # ✅ already effective
        deleted_at__isnull=True
    ).filter(
        end_date__isnull=True
    ) | BenefitEnrollment.objects.filter(
        employee=employee,
        status="ACTIVE",
        effective_date__lte=today,
        end_date__gte=today,
        deleted_at__isnull=True
    )

    deduction = Decimal("0.00")

    for e in enrollments:
        deduction += Decimal(e.employee_monthly_cost or 0)

    return deduction
