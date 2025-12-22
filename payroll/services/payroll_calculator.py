from decimal import Decimal

def calculate_employee_payroll(employee):
    """
    Returns calculated payroll values for one employee
    """

    basic_salary = Decimal(employee.salary or 0)

    # ---- Earnings ----
    house_rent_allowance = basic_salary * Decimal('0.40')   # 40% of basic
    transport_allowance = Decimal('1600')
    other_allowances = Decimal('0')

    gross_salary = (
        basic_salary +
        house_rent_allowance +
        transport_allowance +
        other_allowances
    )

    # ---- Deductions ----
    provident_fund = basic_salary * Decimal('0.12')   # 12%
    professional_tax = Decimal('200')
    income_tax = Decimal('0')  # Phase-2

    total_deductions = (
        provident_fund +
        professional_tax +
        income_tax
    )

    net_salary = gross_salary - total_deductions

    return {
        'basic_salary': basic_salary,
        'house_rent_allowance': house_rent_allowance,
        'transport_allowance': transport_allowance,
        'other_allowances': other_allowances,
        'gross_salary': gross_salary,
        'provident_fund': provident_fund,
        'professional_tax': professional_tax,
        'income_tax': income_tax,
        'total_deductions': total_deductions,
        'net_salary': net_salary
    }
