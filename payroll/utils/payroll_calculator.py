from decimal import Decimal
from payroll.utils.calculator import calculate_overtime

def calculate_employee_payroll(employee, payroll_period):
    """
    Returns calculated payroll values for one employee
    """

    # ---- BASIC ----
    basic_salary = Decimal(str(employee.salary).replace(',', '') or 0)

    # ---- ALLOWANCES ----
    house_rent_allowance = basic_salary * Decimal('0.40')
    transport_allowance = Decimal('1600')
    other_allowances = Decimal('0')

    # ---- OVERTIME ----
    overtime_hours, overtime_rate, overtime_amount = calculate_overtime(
        employee,
        basic_salary,
        payroll_period
    )

    # ---- BONUSES (manual later) ----
    performance_bonus = Decimal('0')
    project_bonus = Decimal('0')

    # ---- GROSS ----
    gross_salary = (
        basic_salary +
        house_rent_allowance +
        transport_allowance +
        other_allowances +
        overtime_amount +
        performance_bonus +
        project_bonus
    )

    # ---- DEDUCTIONS ----
    provident_fund = basic_salary * Decimal('0.12')
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

        'overtime_hours': overtime_hours,
        'overtime_rate': overtime_rate,
        'overtime_amount': overtime_amount,

        'performance_bonus': performance_bonus,
        'project_bonus': project_bonus,

        'gross_salary': gross_salary,

        'provident_fund': provident_fund,
        'professional_tax': professional_tax,
        'income_tax': income_tax,
        'total_deductions': total_deductions,

        'net_salary': net_salary
    }
