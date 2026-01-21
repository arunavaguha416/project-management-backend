from hr_management.models.hr_management_models import Employee
from projects.models.project_member_model import ProjectMember
from hr_management.models.hr_management_models import LeaveRequest
from hr_management.models.hr_management_models import Attendance
from hr_management.utils.attendance_utils import calculate_overtime_hours
from hr_management.models.hr_management_models import Attendance
from projects.utils.sprint_capacity_service import calculate_sprint_capacity

def calculate_avg_overtime(employees, sprint):
    if not sprint.start_date or not sprint.end_date:
        return 0

    total = 0
    count = 0

    for emp in employees:
        attendances = Attendance.objects.filter(
            employee=emp,
            date__range=(sprint.start_date, sprint.end_date)
        )
        total += calculate_overtime_hours(attendances)
        count += 1

    return round(total / max(count, 1), 2)



def calculate_attendance_score(employees, sprint):
    if not sprint.start_date or not sprint.end_date:
        return 100

    sprint_days = (sprint.end_date - sprint.start_date).days + 1
    if sprint_days <= 0:
        return 100

    total_score = 0

    for emp in employees:
        present = Attendance.objects.filter(
            employee=emp,
            date__range=(sprint.start_date, sprint.end_date)
        ).count()
        total_score += (present / sprint_days) * 100

    return round(total_score / max(employees.count(), 1), 1)



def get_project_employees(project):
    """
    Returns active employees assigned to a project
    """
    member_user_ids = ProjectMember.objects.filter(
        project=project,
        is_active=True
    ).values_list("user_id", flat=True)

    return Employee.objects.filter(
        user_id__in=member_user_ids,
        deleted_at__isnull=True
    )



def calculate_leave_ratio(employees, sprint):
    if not sprint or not sprint.start_date or not sprint.end_date:
        return 0

    sprint_days = (sprint.end_date - sprint.start_date).days + 1
    if sprint_days <= 0:
        return 0

    total_leave_days = 0

    for emp in employees:
        leave_days = LeaveRequest.objects.filter(
            employee=emp,
            status="APPROVED",
            start_date__lte=sprint.end_date,
            end_date__gte=sprint.start_date
        ).count()
        total_leave_days += leave_days

    avg_leave = total_leave_days / max(employees.count(), 1)
    return round(min(avg_leave / sprint_days, 1), 2)


def is_manager_on_leave(project, sprint):
    if not project.manager or not sprint.start_date or not sprint.end_date:
        return False

    return LeaveRequest.objects.filter(
        employee=project.manager,
        status="APPROVED",
        start_date__lte=sprint.end_date,
        end_date__gte=sprint.start_date
    ).exists()




def calculate_avg_overtime(employee, sprint):
    attendances = Attendance.objects.filter(
        employee=employee,
        date__range=(sprint.start_date, sprint.end_date)
    )

    total_overtime = calculate_overtime_hours(attendances)
    sprint_days = max(attendances.count(), 1)

    return round(total_overtime / sprint_days, 2)




def is_over_capacity(sprint):
    capacity = calculate_sprint_capacity(sprint)

    planned_points = sum(
        t.story_points or 0
        for t in sprint.tasks.filter(deleted_at__isnull=True)
    )

    return planned_points > capacity.get("total_capacity", 0)

def get_risk_label(score):
    if score >= 85:
        return "LOW"
    if score >= 65:
        return "MEDIUM"
    if score >= 45:
        return "HIGH"
    return "CRITICAL"


def calculate_hr_sprint_risk(project, sprint):
    employees = get_project_employees(project)

    if not employees.exists():
        return {
            "score": 0,
            "risk": "CRITICAL",
            "reason": "No team members assigned"
        }

    leave_penalty = 0
    attendance_score = 0
    overtime_penalty = 0

    for emp in employees:
        leave_penalty += calculate_leave_ratio(emp, sprint) * 20
        attendance_score += calculate_attendance_score(emp, sprint)
        overtime_penalty += min(calculate_avg_overtime(emp, sprint) * 5, 15)

    avg_attendance = attendance_score / employees.count()

    manager_penalty = 15 if is_manager_on_leave(project, sprint) else 0
    capacity_penalty = 20 if is_over_capacity(sprint) else 0

    final_score = max(
        0,
        100
        - leave_penalty
        - overtime_penalty
        - manager_penalty
        - capacity_penalty
        + (avg_attendance - 85)
    )

    final_score = round(min(final_score, 100), 1)

    return {
        "score": final_score,
        "risk": get_risk_label(final_score),
        "signals": {
            "manager_on_leave": manager_penalty > 0,
            "over_capacity": capacity_penalty > 0,
            "avg_attendance": round(avg_attendance, 1)
        }
    }
