from decimal import Decimal
from payroll.utils.attendance import calculate_overtime_hours


def calculate_overtime(employee, basic_salary, period):
    hourly_rate = basic_salary / Decimal(26 * 8)
    overtime_rate = hourly_rate * Decimal('1.5')

    overtime_hours = calculate_overtime_hours(
        employee,
        period.start_date,
        period.end_date
    )

    overtime_amount = overtime_hours * overtime_rate

    return overtime_hours, overtime_rate, overtime_amount
