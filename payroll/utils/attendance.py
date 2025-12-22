from datetime import datetime, timedelta
from decimal import Decimal
from hr_management.models.hr_management_models import Attendance


def calculate_overtime_hours(employee, start_date, end_date):
    """
    Returns total overtime hours for an employee in a payroll period
    """
    attendances = Attendance.objects.filter(
        employee=employee,
        date__range=(start_date, end_date)
    )

    overtime_minutes = 0

    for att in attendances:
        if not att.in_time or not att.out_time:
            continue

        worked_minutes = (
            datetime.combine(att.date, att.out_time) -
            datetime.combine(att.date, att.in_time)
        ).total_seconds() / 60

        standard_minutes = 8 * 60

        if worked_minutes > standard_minutes:
            overtime_minutes += worked_minutes - standard_minutes

    return Decimal(overtime_minutes / 60).quantize(Decimal('0.00'))
