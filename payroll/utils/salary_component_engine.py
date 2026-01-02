from decimal import Decimal
from payroll.models.salary_component import SalaryComponent


def calculate_salary_components(basic_salary: Decimal):
    """
    Returns:
    - earnings_total
    - deductions_total
    - breakdown dict
    """

    components = SalaryComponent.objects.filter(
        deleted_at__isnull=True
    )

    earnings = Decimal("0.00")
    deductions = Decimal("0.00")
    breakdown = {}

    # First pass: BASIC based
    for comp in components:
        amount = Decimal("0.00")

        if comp.calculation_type == "FIXED":
            # FIXED components assumed to be monthly for now
            amount = Decimal("0.00")

        elif comp.calculation_type == "PERCENTAGE":
            if comp.percentage_of == "BASIC":
                amount = (basic_salary * comp.percentage / Decimal("100"))

        breakdown[comp.name] = amount

        if comp.component_type == "EARNING":
            earnings += amount
        else:
            deductions += amount

    gross_salary = basic_salary + earnings

    # Second pass: GROSS based
    for comp in components:
        if comp.calculation_type == "PERCENTAGE" and comp.percentage_of == "GROSS":
            amount = (gross_salary * comp.percentage / Decimal("100"))
            breakdown[comp.name] += amount

            if comp.component_type == "EARNING":
                earnings += amount
            else:
                deductions += amount

    return earnings, deductions, breakdown
