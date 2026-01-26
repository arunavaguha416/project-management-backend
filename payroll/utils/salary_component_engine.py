# payroll/utils/salary_component_engine.py

from decimal import Decimal
from payroll.models.salary_component import SalaryComponent

def calculate_salary_components(basic_salary: Decimal, company=None):
    """
    Returns:
    - component_earnings
    - component_deductions
    - breakdown (dict)
    """

    components = SalaryComponent.objects.filter(
        company=company,
        is_active=True,
        deleted_at__isnull=True
    )

    earnings = Decimal("0.00")
    deductions = Decimal("0.00")
    breakdown = {}

    # BASIC based
    for comp in components:
        amount = Decimal("0.00")

        if comp.calculation_type == "FIXED":
            amount = comp.percentage or Decimal("0.00")

        elif comp.calculation_type == "PERCENTAGE" and comp.percentage_of == "BASIC":
            amount = (basic_salary * comp.percentage) / Decimal("100")

        if amount == 0:
            continue

        breakdown[comp.name] = amount

        if comp.component_type == "EARNING":
            earnings += amount
        else:
            deductions += amount

    gross_salary = basic_salary + earnings

    # GROSS based
    for comp in components:
        if comp.calculation_type == "PERCENTAGE" and comp.percentage_of == "GROSS":
            amount = (gross_salary * comp.percentage) / Decimal("100")
            breakdown[comp.name] = breakdown.get(comp.name, 0) + amount

            if comp.component_type == "EARNING":
                earnings += amount
            else:
                deductions += amount

    return earnings, deductions, breakdown
