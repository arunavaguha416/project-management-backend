from datetime import timedelta
from hr_management.models.hr_management_models import Attendance, LeaveRequest

def calculate_attendance_summary(employee, start_date, end_date):
    """
    Returns:
    {
        working_days,
        present_days,
        paid_leave_days,
        lop_days,
        payable_days
    }
    """

    total_days = (end_date - start_date).days + 1

    # Count present days (attendance exists)
    present_days = Attendance.objects.filter(
        employee=employee,
        date__range=(start_date, end_date)
    ).count()

    # Count approved paid leaves
    paid_leave_days = LeaveRequest.objects.filter(
        employee=employee,
        status="APPROVED",
        start_date__lte=end_date,
        end_date__gte=start_date
    ).count()

    payable_days = present_days + paid_leave_days
    lop_days = max(total_days - payable_days, 0)

    return {
        "working_days": total_days,
        "present_days": present_days,
        "paid_leave_days": paid_leave_days,
        "payable_days": payable_days,
        "lop_days": lop_days,
    }
