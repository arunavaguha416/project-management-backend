from datetime import date
from hr_management.models.hr_management_models import LeaveRequest

def get_leave_summary(employee, year, month):
    leaves = LeaveRequest.objects.filter(
        employee=employee,
        status="APPROVED",
        start_date__year=year,
        start_date__month=month
    )

    paid_leave_days = 0

    for leave in leaves:
        start = max(leave.start_date, date(year, month, 1))
        end = min(leave.end_date, date(year, month, 28))  # safe cap

        days = (end - start).days + 1
        paid_leave_days += max(days, 0)

    return {
        "paid_leave_days": paid_leave_days
    }
