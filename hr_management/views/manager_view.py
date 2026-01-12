from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone
from django.db.models import Q, Avg

from hr_management.models.hr_management_models import (
    Employee,
    Attendance,
    LeaveRequest
)

from hr_management.serializers.hr_management_serializer import EmployeeSerializer
from projects.models.project_model import Project
from projects.models.sprint_model import Sprint
from teams.models.team_members_mapping import TeamMembersMapping
from teams.models.team_model import Team



class ManagerDashboardMetrics(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        # if request.user.role != 'MANAGER':
        #     return Response(
        #         {
        #             'status': False,
        #             'message': 'Only managers can access manager dashboard'
        #         },
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        try:
            today = timezone.now().date()

            # -------------------------------------------------
            # Manager employee
            # -------------------------------------------------
            manager_employee = Employee.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).first()

            if not manager_employee:
                return Response(
                    {
                        'status': False,
                        'message': 'Manager employee record not found'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # -------------------------------------------------
            # Managed projects
            # -------------------------------------------------
            managed_projects = Project.objects.filter(
                manager=manager_employee
            )

            managed_project_ids = managed_projects.values_list('id', flat=True)

            # -------------------------------------------------
            # Teams under managed projects
            # -------------------------------------------------
            teams = Team.objects.filter(
                project_id__in=managed_project_ids
            )

            # -------------------------------------------------
            # Team members (ONLY via TeamMembersMapping)
            # -------------------------------------------------
            team_user_ids = TeamMembersMapping.objects.filter(
                team__in=teams
            ).values_list('user_id', flat=True).distinct()

            team_employees = Employee.objects.filter(
                user_id__in=team_user_ids,
                deleted_at__isnull=True
            ).distinct()

            team_size = team_employees.count()

            # -------------------------------------------------
            # Attendance (today)
            # -------------------------------------------------
            present_today = Attendance.objects.filter(
                employee__in=team_employees,
                date=today
            ).count()

            absent_today = max(team_size - present_today, 0)

            attendance_rate = round(
                (present_today / team_size) * 100, 1
            ) if team_size > 0 else 0

            # -------------------------------------------------
            # Leave signals
            # -------------------------------------------------
            pending_leave_qs = LeaveRequest.objects.filter(
                employee__in=team_employees,
                status='PENDING'
            ).order_by('-created_at')[:5]

            on_leave_today = LeaveRequest.objects.filter(
                employee__in=team_employees,
                status='APPROVED',
                start_date__lte=today,
                end_date__gte=today
            ).count()

            pending_leaves = []
            for leave in pending_leave_qs:
                pending_leaves.append({
                    'id': str(leave.id),
                    'employee_name': leave.employee.user.name if leave.employee.user else 'Unknown',
                    'start_date': leave.start_date.strftime('%Y-%m-%d'),
                    'end_date': leave.end_date.strftime('%Y-%m-%d'),
                    'reason': leave.reason
                })

            # -------------------------------------------------
            # Team member monthly summary
            # -------------------------------------------------
            team_members = []
            for emp in team_employees:
                present_days = Attendance.objects.filter(
                    employee=emp,
                    date__month=today.month,
                    date__year=today.year
                ).count()

                leave_days = LeaveRequest.objects.filter(
                    employee=emp,
                    status='APPROVED',
                    start_date__month=today.month,
                    start_date__year=today.year
                ).count()

                team_members.append({
                    'id': str(emp.id),
                    'name': emp.user.name if emp.user else 'Unknown',
                    'present_days': present_days,
                    'leave_days': leave_days
                })

            # -------------------------------------------------
            # Sprint & workload signals
            # -------------------------------------------------
            active_projects = managed_projects.filter(
                status='Ongoing'
            ).count()

            active_sprints = Sprint.objects.filter(
                project_id__in=managed_project_ids,
                status='ACTIVE'
            )

            avg_velocity = active_sprints.aggregate(
                Avg('velocity')
            )['velocity__avg'] or 0

            if avg_velocity >= 40:
                risk_level = 'LOW'
            elif avg_velocity >= 20:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'

            # -------------------------------------------------
            # Final response payload
            # -------------------------------------------------
            data = {
                'metrics': {
                    'team_size': team_size,
                    'attendance_rate': attendance_rate,
                    'on_leave_today': on_leave_today,
                    'pending_approvals': len(pending_leaves)
                },
                'attendance_summary': {
                    'present': present_today,
                    'absent': absent_today
                },
                'pending_leaves': pending_leaves,
                'team_members': team_members,
                'workload': {
                    'active_projects': active_projects,
                    'active_sprints': active_sprints.count(),
                    'avg_velocity': round(avg_velocity),
                    'risk_level': risk_level
                }
            }

            return Response(
                {
                    'status': True,
                    'records': data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    'status': False,
                    'message': 'Failed to load manager dashboard metrics',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        




class ManagerList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try: 
            # Fix 1: Properly assign the Q object to query
            # Fix 2: Correct 'icontain' to 'icontains'
            # Fix 3: Use &= to apply the filter to query
            query = Q(user__role__icontains="MANAGER")

            employees = Employee.objects.filter(query).order_by('-created_at')

            if employees.exists():               
                serializer = EmployeeSerializer(employees, many=True)
                return Response({
                    'status': True,                    
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No managers found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        


