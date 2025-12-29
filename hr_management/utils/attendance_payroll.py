# hr_management/utils/attendance_payroll.py

from hr_management.models.hr_management_models import Attendance
from calendar import monthrange
from datetime import date, datetime

def get_attendance_summary(employee, year, month):
    total_days = monthrange(year, month)[1]
    working_days = sum(
        1 for d in range(1, total_days + 1)
        if date(year, month, d).weekday() < 5
    )

    attendances = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    )

    present_days = attendances.count()
    absent_days = max(working_days - present_days, 0)

    overtime_hours = 0.0
    for a in attendances:
        if a.in_time and a.out_time:
            hours = (
                datetime.combine(date.today(), a.out_time)
                - datetime.combine(date.today(), a.in_time)
            ).seconds / 3600
            if hours > 8:
                overtime_hours += (hours - 8)

    return {
        "working_days": working_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "overtime_hours": round(overtime_hours, 2)
    }
