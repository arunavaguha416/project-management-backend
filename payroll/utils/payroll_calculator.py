from decimal import Decimal
from payroll.utils.calculator import calculate_overtime
from payroll.utils.tax_engine import calculate_monthly_tax
from payroll.utils.salary_component_engine import calculate_salary_components
from payroll.utils.benefits_engine import calculate_benefit_deductions


def calculate_employee_payroll(employee, payroll_period):
    # ---- BASIC ----
    basic_salary = Decimal(str(employee.salary).replace(',', '') or 0)

    # ---- SALARY COMPONENTS ----
    component_earnings, component_deductions, component_breakdown = (
        calculate_salary_components(basic_salary)
    )

    # ---- EXISTING ALLOWANCES (KEEP) ----
    house_rent_allowance = basic_salary * Decimal('0.40')
    transport_allowance = Decimal('1600')
    other_allowances = Decimal('0')

    # ---- OVERTIME ----
    overtime_hours, overtime_rate, overtime_amount = calculate_overtime(
        employee,
        basic_salary,
        payroll_period
    )

    # ---- GROSS ----
    gross_salary = (
        basic_salary +
        house_rent_allowance +
        transport_allowance +
        other_allowances +
        component_earnings +
        overtime_amount
    )

    # ---- TAX ----
    income_tax = calculate_monthly_tax(gross_salary)

    # ---- DEDUCTIONS ----
    provident_fund = basic_salary * Decimal('0.12')
    professional_tax = Decimal('200')
    benefit_deductions = calculate_benefit_deductions(employee)

    total_deductions = (
        provident_fund +
        professional_tax +
        income_tax +
        component_deductions +
        benefit_deductions
    )

    net_salary = gross_salary - total_deductions

    return {
        # KEEP EXISTING RETURNS (unchanged)
        "basic_salary": basic_salary,
        "house_rent_allowance": house_rent_allowance,
        "transport_allowance": transport_allowance,
        "other_allowances": other_allowances,

        "overtime_hours": overtime_hours,
        "overtime_rate": overtime_rate,
        "overtime_amount": overtime_amount,

        "gross_salary": gross_salary,

        "provident_fund": provident_fund,
        "professional_tax": professional_tax,
        "income_tax": income_tax,
        "total_deductions": total_deductions,

        "net_salary": net_salary,

        # NEW (OPTIONAL, SAFE)
        "component_breakdown": component_breakdown
    }