# payroll/utils/form16_utils.py

from django.db import models
from payroll.models import Payroll
from payroll.utils.date_utils import get_financial_year


def generate_form16_summary(employee, financial_year):
    """
    Aggregates FINALIZED payrolls for a given employee and FY
    """
    start_year, end_year = map(int, financial_year.split("-"))

    payrolls = Payroll.objects.filter(
        employee=employee,
        pay_run__status="FINALIZED",
        payroll_period__start_date__year__in=[start_year, end_year],
        deleted_at__isnull=True
    )

    aggregates = payrolls.aggregate(
        gross_salary=models.Sum("gross_salary") or 0,
        income_tax=models.Sum("income_tax") or 0,
        provident_fund=models.Sum("provident_fund") or 0,
        professional_tax=models.Sum("professional_tax") or 0,
        total_deductions=models.Sum("total_deductions") or 0,
        net_salary=models.Sum("net_salary") or 0,
    )

    taxable_income = (
        aggregates["gross_salary"]
        - aggregates["provident_fund"]
        - aggregates["professional_tax"]
    )

    return {
        "gross_salary": aggregates["gross_salary"] or 0,
        "taxable_income": taxable_income or 0,
        "total_tax": aggregates["income_tax"] or 0,
        "provident_fund": aggregates["provident_fund"] or 0,
        "professional_tax": aggregates["professional_tax"] or 0,
        "net_salary": aggregates["net_salary"] or 0,
    }
