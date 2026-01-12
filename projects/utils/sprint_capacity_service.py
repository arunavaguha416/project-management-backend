# projects/utils/sprint_capacity_service.py

from datetime import date
from django.db.models import Sum
from django.utils import timezone

from hr_management.models.hr_management_models import Attendance, LeaveRequest, Employee
from projects.models.task_model import Task
from hr_management.utils.attendance_utils import calculate_working_days


def calculate_sprint_capacity(sprint):
    """
    Returns sprint-level + per-assignee capacity
    """

    start = sprint.start_date
    end = sprint.end_date

    if not start or not end:
        return {
            "total_capacity": 0,
            "assignees": []
        }

    year = start.year
    month = start.month

    sprint_days = calculate_working_days(year, month)

    # Tasks already in sprint
    tasks = Task.objects.filter(
        sprint=sprint,
        deleted_at__isnull=True
    )

    assignee_ids = tasks.values_list("assigned_to", flat=True).distinct()

    assignees_data = []
    sprint_total_capacity = 0

    for emp_id in assignee_ids:
        if not emp_id:
            continue

        employee = Employee.objects.filter(id=emp_id, deleted_at__isnull=True).first()
        if not employee:
            continue

        # ---- Leaves during sprint ----
        leave_days = LeaveRequest.objects.filter(
            employee=employee,
            status="APPROVED",
            start_date__lte=end,
            end_date__gte=start
        ).count()

        # ---- Attendance buffer (simple v1) ----
        attendance_days = Attendance.objects.filter(
            employee=employee,
            date__range=(start, end)
        ).count()

        expected_absence = max(sprint_days - attendance_days, 0)

        effective_days = max(
            sprint_days - leave_days - expected_absence,
            0
        )

        # ---- Velocity fallback ----
        daily_velocity = (sprint.velocity or 0) / max(sprint_days, 1)

        capacity_points = round(effective_days * daily_velocity, 1)

        sprint_total_capacity += capacity_points

        assignees_data.append({
            "employee_id": str(employee.id),
            "name": employee.user.name if employee.user else "Unknown",
            "effective_days": effective_days,
            "capacity_points": capacity_points,
            "leave_days": leave_days,
            "attendance_days": attendance_days
        })

    return {
        "total_capacity": round(sprint_total_capacity, 1),
        "assignees": assignees_data
    }
