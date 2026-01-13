from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from django.db.models import Avg

from hr_management.models.hr_management_models import (
    Employee,
    Attendance,
    LeaveRequest,
    LeaveBalance
)


from projects.models.sprint_model import Sprint
from projects.models.task_model import Task



def generate_focus_explanation(task):
    reasons = []

    today = timezone.now().date()

    if task.due_date and task.due_date < today:
        reasons.append("This task is overdue")

    if task.priority in ['HIGH', 'CRITICAL']:
        reasons.append("It has high priority")

    if task.progress_percentage is not None and task.progress_percentage < 40:
        reasons.append("Progress is still low")

    return " • ".join(reasons) if reasons else (
        "This task needs attention based on sprint workload"
    )




class EmployeeDashboardMetrics(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            today = timezone.now().date()

            # -------------------------------------------------
            # Employee (HR domain)
            # -------------------------------------------------
            employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # -------------------------------------------------
            # Attendance
            # -------------------------------------------------
            attendance_today = Attendance.objects.filter(
                employee=employee,
                date=today
            ).exists()

            # -------------------------------------------------
            # Leave
            # -------------------------------------------------
            leave_balance, _ = LeaveBalance.objects.get_or_create(
                employee=employee,
                defaults={'balance': 24}
            )

            on_leave_today = LeaveRequest.objects.filter(
                employee=employee,
                status='APPROVED',
                start_date__lte=today,
                end_date__gte=today
            ).exists()

            pending_leaves = LeaveRequest.objects.filter(
                employee=employee,
                status='PENDING'
            ).count()

            # -------------------------------------------------
            # Projects → Active Sprint
            # -------------------------------------------------
            teams = []

            project_ids = teams.values_list('project_id', flat=True)

            active_sprint = Sprint.objects.filter(
                project_id__in=project_ids,
                status='ACTIVE'
            ).first()

            sprint_tasks = {
                'active_sprint': None,
                'active_sprint_id': None,
                'total_tasks': 0,
                'completed': 0,
                'pending': 0
            }

            pending_tasks_today = 0

            if active_sprint:
                tasks_qs = Task.objects.filter(
                    sprint=active_sprint,
                    assigned_to=request.user   # ✅ FIXED
                )

                completed = tasks_qs.filter(status='DONE').count()
                total = tasks_qs.count()
                pending = total - completed

                pending_tasks_today = pending

                sprint_tasks = {
                    'active_sprint': active_sprint.name,
                    'project_id' :active_sprint.project_id,
                    'active_sprint_id': str(active_sprint.id),
                    'total_tasks': total,
                    'completed': completed,
                    'pending': pending
                }

            # -------------------------------------------------
            # Workload (velocity)
            # -------------------------------------------------
            avg_velocity = Sprint.objects.filter(
                project_id__in=project_ids,
                status='ACTIVE'
            ).aggregate(Avg('velocity'))['velocity__avg'] or 0

            if avg_velocity >= 40:
                risk = 'LOW'
            elif avg_velocity >= 20:
                risk = 'MEDIUM'
            else:
                risk = 'HIGH'

            # -------------------------------------------------
            # Today Checklist
            # -------------------------------------------------
            today_checklist = {
                'checked_in': attendance_today,
                'has_tasks_today': pending_tasks_today > 0,
                'pending_tasks': pending_tasks_today,
                'on_leave': on_leave_today
            }

            # -------------------------------------------------
            # Overdue Tasks (USER domain)
            # -------------------------------------------------
            overdue_tasks_qs = Task.objects.filter(
                assigned_to=request.user,
                due_date__lt=today
            ).exclude(status='DONE').order_by('due_date')[:5]

            overdue_tasks = [{
                'id': str(t.id),
                'title': t.title,
                'priority': t.priority,
                'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None,
                'sprint_id': str(t.sprint.id) if t.sprint else None
            } for t in overdue_tasks_qs]

            # -------------------------------------------------
            # AI Focus Task
            # -------------------------------------------------
            focus_task = Task.objects.filter(
                assigned_to=request.user,
                sprint__status='ACTIVE'
            ).exclude(status='DONE').order_by(
                'due_date',
                '-priority',
                'progress_percentage'
            ).first()

            ai_focus_task = None
            if focus_task:
                ai_focus_task = {
                    'id': str(focus_task.id),
                    'title': focus_task.title,
                    'priority': focus_task.priority,
                    'status': focus_task.status,
                    'due_date': (
                        focus_task.due_date.strftime('%Y-%m-%d')
                        if focus_task.due_date else None
                    ),
                    'sprint_id': (
                        str(focus_task.sprint.id)
                        if focus_task.sprint else None
                    ),
                    'explanation': generate_focus_explanation(focus_task)
                }

            # -------------------------------------------------
            # Final Response
            # -------------------------------------------------
            data = {
                'attendance': {'checked_in': attendance_today},
                'leave': {
                    'balance': leave_balance.balance,
                    'pending': pending_leaves,
                    'on_leave_today': on_leave_today
                },
                'workload': {'risk_level': risk},
                'today_checklist': today_checklist,
                'sprint_tasks': sprint_tasks,
                'overdue_tasks': overdue_tasks,
                'ai_focus_task': ai_focus_task
            }

            return Response({
                'status': True,
                'records': data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load employee dashboard',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


