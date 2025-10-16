from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from hr_management.models.hr_management_models import *
from hr_management.serializers.hr_management_serializer import *
from django.core.paginator import Paginator
from datetime import timedelta
from projects.models.project_model import Project, UserMapping
from django.utils import timezone
from projects.models.project_model import Project
from authentication.models.user import User
from hr_management.models.hr_management_models import Attendance
from teams.models.team_model import Team
from teams.models.team_members_mapping import TeamMembersMapping

# Employee Views
class EmployeeAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            serializer = EmployeeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Employee added successfully',
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': ('An error occurred while adding the employee'),
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page', 1)
            page_size = int(search_data.get('page_size', 10))
            search_employee = search_data.get('search', '')

            query = Q()
            if search_employee:
                # Search across Employee model fields AND related User fields
                query &= (
                    Q(user__name__icontains=search_employee)
                    | Q(user__username__icontains=search_employee)
                    | Q(user__email__icontains=search_employee)
                    
                ) & Q(user__role__icontains="MANAGER")

            employees = Employee.objects.filter(query).order_by('-created_at')

            if employees.exists():
                paginator = Paginator(employees, page_size)
                try:
                    paginated_employees = paginator.page(page)
                except Exception:
                    paginated_employees = paginator.page(1)
                serializer = EmployeeSerializer(paginated_employees, many=True)
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Employees not found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        
class DeletedEmployeeList(APIView):
    permission_classes=(IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', '')
            search_department = search_data.get('department', '')

            query = Q(deleted_at__isnull=False)
            if search_department:
                query &= Q(department__icontains=search_department)

            employees = Employee.all_objects.filter(query).order_by('-created_at')

            if employees.exists():
                if page is not None:
                    paginator = Paginator(employees, page_size)
                    paginatedEmployees = paginator.get_paginator(page)
                    serializer = EmployeeSerializer(paginatedEmployees, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = EmployeeSerializer(employees, many=True)
                    return Response({
                        'status': True,
                        'count': employees.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted employees not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            employee_id = request.data.get('id')
            if employee_id:
                employee = Employee.objects.filter(id=employee_id).values('id', 'user__username', 'department', 'phone').first()
                if employee:
                    return Response({
                        'status': True,
                        'records': employee
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Employee not found',
                    }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Please provide employeeId'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching employee details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            employee_id = request.data.get('id')
            employee = Employee.objects.filter(id=employee_id).first()
            if employee:
                serializer = EmployeeSerializer(employee, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Employee updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Employee not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the employee',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeDelete(APIView):
    permission_classes = [IsAuthenticated,]

    def delete(self, request, employee_id):
        try:
            employee = Employee.objects.filter(id=employee_id).first()
            if employee:
                employee.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Employee deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Employee not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreEmployee(APIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request):
        try:
            employee_id = request.data.get('id')
            employee = Employee.all_objects.get(id=employee_id)
            if employee:
                employee.deleted_at = None
                employee.save()
                return Response({
                    'status': True,
                    'message': 'Employee restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Employee not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)




# --- 3. Attendance Summary ---
class AttendanceSummary(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        emp_qs = Employee.objects.filter(deleted_at__isnull=True)
        total = emp_qs.count()
        today = timezone.now().date()
        leaves_today = LeaveRequest.objects.filter(
            start_date__lte=today, end_date__gte=today, status="APPROVED"
        ).values_list('employee_id', flat=True)
        present = total - leaves_today.count()
        absent = leaves_today.count()
        attendance = {
            "present": present,
            "absent": absent,
            "present_percent": round((present / total) * 100 if total else 0),
            "absent_percent": round((absent / total) * 100 if total else 0),
        }
        return Response(attendance)


# --- 4. Upcoming Birthdays (next 30 days, top N) ---
class BirthdayList(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            today = timezone.now().date()
            next_month = today + timedelta(days=30)
            search = request.data.get('search', '').strip()
            page = int(request.data.get('page', 1))
            page_size = int(request.data.get('page_size', 10))

            # All users with DOB set
            qs = User.objects.filter(is_active=True, date_of_birth__isnull=False)

            # Find users with birthdays in next 30 days
            matches = []
            for u in qs:
                dob = u.date_of_birth
                try:
                    dob_this_year = dob.replace(year=today.year)
                except ValueError:
                    # Handles Feb 29 on non-leap years
                    continue

                if today <= dob_this_year <= next_month:
                    if search:
                        if (search.lower() in (u.name or '').lower()) or (search.lower() in (u.email or '').lower()):
                            matches.append(u)
                    else:
                        matches.append(u)

            total = len(matches)
            paginator = Paginator(matches, page_size)
            try:
                paginated_birthdays = paginator.page(page)
            except Exception:
                paginated_birthdays = paginator.page(1)

            records = [
                {
                    'name': u.name,
                    'email': u.email,
                    'date': str(u.date_of_birth)
                }
                for u in paginated_birthdays
            ]

            if total > 0:
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'records': records
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No birthdays found',
                    'count': 0,
                    'num_pages': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
  
class EmployeeAttendanceList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get employee ID from request data
            employee_id = request.data.get('employee_id')
            page_size = request.data.get('page_size', 10)
            search = request.data.get('search', '').strip()
            date_from = request.data.get('date_from')
            date_to = request.data.get('date_to')
            
            if not employee_id:
                return Response({
                    'status': False,
                    'message': 'Employee ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # First get the user from User table
            user = User.objects.filter(id=employee_id).first()
            if not user:
                return Response({
                    'status': False,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get employee record related to this user
            employee = Employee.objects.filter(user=user).first()
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found for this user'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check permissions - users can only view their own attendance unless HR/Admin
            if request.user.role not in ['HR', 'ADMIN'] and request.user.id != user.id:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions to view this attendance record'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Build query for attendance records
            query = Q(employee=employee)
            
            # Apply date range filter
            if date_from:
                query &= Q(date__gte=date_from)
            if date_to:
                query &= Q(date__lte=date_to)
            
            # Apply search filter (if searching by date or status)
            if search:
                query &= Q(date__icontains=search)
            
            # Get attendance records
            attendances = Attendance.objects.filter(query).order_by('-date')
            
            # Apply pagination
            if page_size:
                attendances = attendances[:int(page_size)]
            
            # Enhanced attendance data with calculations
            attendance_data = []
            total_present_days = 0
            total_hours_worked = 0
            
            for attendance in attendances:
                hours_worked = self.calculate_hours_worked(attendance.in_time, attendance.out_time)
                if hours_worked:
                    total_hours_worked += hours_worked
                
                status_value = 'PRESENT' if attendance.in_time else 'ABSENT'
                if status_value == 'PRESENT':
                    total_present_days += 1
                
                attendance_data.append({
                    'id': str(attendance.id),
                    'date': attendance.date.strftime('%Y-%m-%d') if attendance.date else None,
                    'check_in': attendance.in_time.strftime('%H:%M:%S') if attendance.in_time else None,
                    'check_out': attendance.out_time.strftime('%H:%M:%S') if attendance.out_time else None,
                    'hours_worked': hours_worked,
                    'status': status_value,
                    'created_at': attendance.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(attendance, 'created_at') and attendance.created_at else None
                })
            
            # Summary statistics
            summary = {
                'total_records': len(attendance_data),
                'total_present_days': total_present_days,
                'total_absent_days': len(attendance_data) - total_present_days,
                'total_hours_worked': round(total_hours_worked, 2),
                'average_hours_per_day': round(total_hours_worked / max(total_present_days, 1), 2) if total_present_days > 0 else 0
            }
            
            return Response({
                'status': True,
                'message': 'Attendance records retrieved successfully',
                'count': len(attendance_data),
                'records': attendance_data,
                'summary': summary,
                'employee': {
                    'id': str(employee.id),
                    'name': user.name,
                    'designation': employee.designation,
                    'department': employee.department.name if employee.department else None
                },
                'filters': {
                    'date_from': date_from,
                    'date_to': date_to,
                    'search': search,
                    'page_size': page_size
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching attendance records',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def calculate_hours_worked(self, in_time, out_time):
        """Helper method to calculate hours worked"""
        if in_time and out_time:
            from datetime import datetime, timedelta
            
            # Convert time objects to datetime for calculation
            today = datetime.today().date()
            in_datetime = datetime.combine(today, in_time)
            out_datetime = datetime.combine(today, out_time)
            
            # Handle case where out_time is next day
            if out_time < in_time:
                out_datetime += timedelta(days=1)
            
            duration = out_datetime - in_datetime
            hours = duration.total_seconds() / 3600
            return round(hours, 2)
        return None

class EmployeeProjectList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_project = search_data.get('search', '').strip()
            
            # Get user from token
            user = request.user
            
            # Get employee associated with the user
            employee = Employee.objects.filter(user=user).first()
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee not found for this user'
                }, status=status.HTTP_404_NOT_FOUND)
            
            from projects.models.project_model import Project, UserMapping
            
            # Build query to find projects where EMPLOYEE is involved
            project_query = (
                Q(owner=employee) |      # Compare with employee, not user
                Q(manager=employee) |    # Compare with employee, not user
                Q(resource=employee)     # Compare with employee, not user
            )
            
            # Projects where employee is mapped through UserMapping
            try:
                mapped_projects = UserMapping.objects.filter(
                    employee=employee
                ).values_list('project_id', flat=True)
                
                if mapped_projects:
                    project_query |= Q(id__in=mapped_projects)
            except Exception as mapping_error:
                print(f"UserMapping error: {mapping_error}")
                pass
            
            # Apply search filter if provided
            if search_project:
                project_query &= (
                    Q(name__icontains=search_project) |
                    Q(description__icontains=search_project)
                )
            
            projects = Project.objects.filter(project_query).distinct().order_by('-created_at')
            
            if projects.exists():
                paginator = Paginator(projects, page_size)
                try:
                    paginated_projects = paginator.page(page)
                except Exception:
                    paginated_projects = paginator.page(1)
                
                project_data = []
                for project in paginated_projects:
                    # Determine employee's role in the project
                    role = []
                    if project.owner == employee:
                        role.append('Owner')
                    if project.manager == employee:
                        role.append('Manager')
                    if project.resource == employee:
                        role.append('Resource')
                    
                    # Check if employee is mapped to project
                    try:
                        if UserMapping.objects.filter(project=project, employee=employee).exists():
                            role.append('Team Member')
                    except Exception as role_error:
                        print(f"Role checking error: {role_error}")
                        pass
                    
                    project_info = {
                        'id': str(project.id),
                        'name': project.name,
                        'description': project.description,
                        'status': project.status,
                        'company': project.company.name if project.company else None,
                        'owner': project.owner.user.name if project.owner and project.owner.user else None,
                        'manager': project.manager.user.name if project.manager and project.manager.user else None,
                        'user_role': ', '.join(role) if role else 'No Role',
                        'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    project_data.append(project_info)
                
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'employee_name': employee.user.name if employee.user else 'Unknown',
                    'records': project_data
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': False,
                    'message': 'No projects found for this employee',
                    'count': 0,
                    'employee_name': employee.user.name if employee.user else 'Unknown',
                    'records': []
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching employee projects',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

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
        

class ManagerDashboardMetrics(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            employee = Employee.objects.filter(user=user).first()
            
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get projects managed by this manager
            managed_projects = Project.objects.filter(manager=employee)
            
            # Get teams for managed projects
            teams_for_managed_projects = Team.objects.filter(
                project_id__in=managed_projects
            ).distinct()
            
            # Count unique team members across all managed project teams
            team_members_count = TeamMembersMapping.objects.filter(
                team__in=teams_for_managed_projects
            ).values('user').distinct().count()
            
            # Count pending leave requests (placeholder)
            pending_leaves = 0  # Update when leave management is implemented
            
            metrics = {
                'total_projects': managed_projects.count(),
                'active_projects': managed_projects.filter(status='Ongoing').count(),
                'completed_projects': managed_projects.filter(status='Completed').count(),
                'team_size': team_members_count,
                'pending_leaves': pending_leaves
            }
            
            return Response({
                'status': True,
                'data': metrics
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching dashboard metrics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        

class GetAvailableManagers(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check user permissions
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get search parameters
            search_data = request.data
            search_name = search_data.get('search', '').strip()
            
            # Build query for managers
            query = Q(user__role__icontains="MANAGER")
            
            if search_name:
                query &= (
                    Q(user__name__icontains=search_name) |
                    Q(user__username__icontains=search_name) |
                    Q(user__email__icontains=search_name)
                )
            
            managers = Employee.objects.filter(query).order_by('user__name')
            
            if managers.exists():
                serializer = EmployeeSerializer(managers, many=True)
                return Response({
                    'status': True,
                    'count': managers.count(),
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
                'message': 'An error occurred while fetching managers',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ProjectAssignmentHistory(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            
            if not project_id:
                return Response({
                    'status': False,
                    'message': 'Project ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get project
            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get project assignment history (if you have an audit log model)
            # This is a placeholder - implement based on your audit log structure
            history_data = {
                'project_id': project.id,
                'project_name': project.name,
                'current_manager': {
                    'id': project.manager.id if project.manager else None,
                    'name': project.manager.user.name if project.manager and project.manager.user else 'Unassigned'
                },
                'status': project.status,
                'last_updated': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return Response({
                'status': True,
                'records': history_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching assignment history',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class BulkAssignProjects(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check permissions
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            assignments = request.data.get('assignments', [])
            
            if not assignments:
                return Response({
                    'status': False,
                    'message': 'No assignments provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            successful_assignments = []
            failed_assignments = []
            
            for assignment in assignments:
                project_id = assignment.get('project_id')
                manager_id = assignment.get('manager_id')
                
                try:
                    # Get project and manager
                    project = Project.objects.get(id=project_id)
                    manager = Employee.objects.get(id=manager_id, user__role='MANAGER')
                    
                    # Check if project can be assigned
                    if project.status in ['Ongoing', 'PENDING']:
                        project.manager = manager
                        project.save()
                        
                        successful_assignments.append({
                            'project_id': project.id,
                            'project_name': project.name,
                            'manager_name': manager.user.name if manager.user else 'Unknown'
                        })
                    else:
                        failed_assignments.append({
                            'project_id': project_id,
                            'reason': 'Project is not in assignable status'
                        })
                        
                except Project.DoesNotExist:
                    failed_assignments.append({
                        'project_id': project_id,
                        'reason': 'Project not found'
                    })
                except Employee.DoesNotExist:
                    failed_assignments.append({
                        'project_id': project_id,
                        'reason': 'Manager not found'
                    })
            
            return Response({
                'status': True,
                'message': f'{len(successful_assignments)} projects assigned successfully',
                'successful_assignments': successful_assignments,
                'failed_assignments': failed_assignments
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred during bulk assignment',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


 

class LeaveRequestsList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Check if user has permission (HR or MANAGER)
            if user.role not in ['HR', 'MANAGER', 'EMPLOYEE']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get request parameters
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            status_filter = search_data.get('status', '').strip()
            search_term = search_data.get('search', '').strip()
            employee_id = search_data.get('employee_id')
            
            # Build base query
            query = Q()
            team_info = {}
            
            if user.role == 'HR':
                # HR can see ALL leave requests
                query = Q()
                team_info['scope'] = 'All Employees'
                team_info['total_employees'] = Employee.objects.filter(deleted_at__isnull=True).count()
                
            elif user.role == 'MANAGER':
                # MANAGER can only see their team members' requests
                manager_employee = Employee.objects.filter(user=user).first()
                if not manager_employee:
                    return Response({
                        'status': False,
                        'message': 'Manager employee record not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get all projects managed by this manager
                managed_projects = Project.objects.filter(manager=manager_employee)
                
                # Get team members from managed projects
                team_members_query = TeamMembersMapping.objects.filter(
                    team__project_id__in=managed_projects
                ).values_list('user_id', flat=True).distinct()
                
                # Get employees who are team members or resources
                team_employees = Employee.objects.filter(
                    Q(user_id__in=team_members_query) |
                    Q(id__in=managed_projects.values_list('resource_id', flat=True)),
                    deleted_at__isnull=True
                ).distinct()
                
                query = Q(employee__in=team_employees)
                team_info['scope'] = 'Your Team Members'
                team_info['total_employees'] = team_employees.count()
                
            elif user.role == 'EMPLOYEE':
                # EMPLOYEE can only see their own requests
                employee = Employee.objects.filter(user=user).first()
                if not employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                query = Q(employee=employee)
                team_info['scope'] = 'My Requests'
            
            # Apply additional filters
            if employee_id and user.role != 'EMPLOYEE':
                query &= Q(employee_id=employee_id)
                
            if status_filter:
                query &= Q(status__iexact=status_filter)
            
            if search_term:
                query &= (
                    Q(employee__user__name__icontains=search_term) |
                    Q(employee__user__email__icontains=search_term) |
                    Q(reason__icontains=search_term)
                )
            
            # Get leave requests with employee details
            leave_requests = LeaveRequest.objects.select_related(
                'employee__user',
                'employee__department'
            ).filter(query).order_by('-created_at')
            
            # Apply pagination
            if leave_requests.exists():
                paginator = Paginator(leave_requests, page_size)
                try:
                    paginated_requests = paginator.page(page)
                except Exception:
                    paginated_requests = paginator.page(1)
                
                # ✅ BUILD SERIALIZABLE DATA - NO DIRECT USER OBJECTS
                leave_data = []
                stats = {
                    'total_requests': 0,
                    'approved': 0,
                    'rejected': 0,
                    'pending': 0,
                    'total_days_requested': 0,
                    'total_days_approved': 0
                }
                
                for leave in paginated_requests:
                    # Calculate days requested
                    days_requested = 0
                    if leave.start_date and leave.end_date:
                        days_requested = (leave.end_date - leave.start_date).days + 1
                    
                    # Get employee's current leave balance
                    try:
                        leave_balance_obj = LeaveBalance.objects.get(employee=leave.employee)
                        current_balance = leave_balance_obj.balance
                    except LeaveBalance.DoesNotExist:
                        current_balance = 24
                    
                    # ✅ SERIALIZE USER DATA MANUALLY - AVOID DIRECT USER OBJECT
                    employee_data = {
                        'id': str(leave.employee.id),
                        'name': leave.employee.user.name if leave.employee.user else 'Unknown',
                        'email': leave.employee.user.email if leave.employee.user else None,
                        'username': leave.employee.user.username if leave.employee.user else None,
                        'designation': leave.employee.designation,
                        'department': leave.employee.department.name if leave.employee.department else None,
                        'leave_balance': current_balance
                    }
                    
                    # ✅ BUILD CLEAN SERIALIZABLE DATA
                    request_data = {
                        'id': str(leave.id),
                        'employee_id': str(leave.employee.id),
                        'employee_name': employee_data['name'],
                        'employee_email': employee_data['email'],
                        'employee_username': employee_data['username'],
                        'designation': employee_data['designation'],
                        'department': employee_data['department'],
                        'employee_leave_balance': employee_data['leave_balance'],
                        'start_date': leave.start_date.strftime('%Y-%m-%d') if leave.start_date else None,
                        'end_date': leave.end_date.strftime('%Y-%m-%d') if leave.end_date else None,
                        'days_requested': days_requested,
                        'reason': leave.reason,
                        'status': leave.status,
                        'applied_on': leave.created_at.strftime('%Y-%m-%d %H:%M:%S') if leave.created_at else None,
                        'can_approve': leave.status == 'PENDING',
                    }
                    
                    # ✅ ADD APPROVAL INFO IF EXISTS (SERIALIZE SAFELY)
                    if hasattr(leave, 'approved_by') and leave.approved_by:
                        request_data['approved_by'] = {
                            'name': leave.approved_by.name if leave.approved_by.name else 'Unknown',
                            'email': leave.approved_by.email if leave.approved_by.email else None
                        }
                    else:
                        request_data['approved_by'] = None
                    
                    if hasattr(leave, 'comments'):
                        request_data['comments'] = leave.comments
                    
                    leave_data.append(request_data)
                    
                    # Update statistics
                    stats['total_requests'] += 1
                    stats['total_days_requested'] += days_requested
                    
                    if leave.status == 'APPROVED':
                        stats['approved'] += 1
                        stats['total_days_approved'] += days_requested
                    elif leave.status == 'REJECTED':
                        stats['rejected'] += 1
                    elif leave.status == 'PENDING':
                        stats['pending'] += 1
                
                return Response({
                    'status': True,
                    'message': 'Leave requests retrieved successfully',
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': leave_data,  # ✅ CLEAN SERIALIZABLE DATA
                    'stats': stats,
                    'user_info': {
                        'role': user.role,
                        'name': user.name,
                        **team_info
                    },
                    'filters': {
                        'status': status_filter,
                        'search': search_term,
                        'employee_id': employee_id,
                        'page_size': page_size
                    }
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': False,
                    'message': 'No leave requests found',
                    'count': 0,
                    'num_pages': 0,
                    'records': [],
                    'stats': {
                        'total_requests': 0,
                        'approved': 0,
                        'rejected': 0,
                        'pending': 0,
                        'total_days_requested': 0,
                        'total_days_approved': 0
                    },
                    'user_info': {
                        'role': user.role,
                        'name': user.name,
                        **team_info
                    }
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching leave requests',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ApplyLeave(APIView):
    """
    Function 2: Single function for HR, MANAGER and EMPLOYEE to apply leave
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Get request data
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            reason = request.data.get('reason', '').strip()
            employee_id = request.data.get('employee_id')  # Optional: for HR/MANAGER to apply on behalf
            
            # Validation
            if not start_date or not end_date or not reason:
                return Response({
                    'status': False,
                    'message': 'start_date, end_date, and reason are required fields'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Determine which employee to apply leave for
            target_employee = None
            
            if employee_id and user.role in ['HR', 'MANAGER']:
                # HR/MANAGER applying on behalf of employee
                target_employee = Employee.objects.filter(id=employee_id).first()
                if not target_employee:
                    return Response({
                        'status': False,
                        'message': 'Employee not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # For MANAGER, verify the employee is in their team
                if user.role == 'MANAGER':
                    manager_employee = Employee.objects.filter(user=user).first()
                    if manager_employee:
                        managed_projects = Project.objects.filter(manager=manager_employee)
                        team_members = TeamMembersMapping.objects.filter(
                            team__project_id__in=managed_projects
                        ).values_list('user_id', flat=True)
                        
                        if target_employee.user_id not in team_members:
                            return Response({
                                'status': False,
                                'message': 'You can only apply leave for your team members'
                            }, status=status.HTTP_403_FORBIDDEN)
            else:
                # User applying for themselves
                target_employee = Employee.objects.filter(user=user).first()
                if not target_employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found for current user'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Date validation
            from datetime import datetime
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'status': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if start_date_obj > end_date_obj:
                return Response({
                    'status': False,
                    'message': 'End date must be after or equal to start date'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate days requested
            days_requested = (end_date_obj - start_date_obj).days + 1
            
            # Check leave balance
            try:
                leave_balance_obj = LeaveBalance.objects.get(employee=target_employee)
                current_balance = leave_balance_obj.balance
            except LeaveBalance.DoesNotExist:
                # Create default balance if doesn't exist
                leave_balance_obj = LeaveBalance.objects.create(
                    employee=target_employee,
                    balance=24
                )
                current_balance = 24
            
            if days_requested > current_balance:
                return Response({
                    'status': False,
                    'message': f'Insufficient leave balance. Available: {current_balance} days, Requested: {days_requested} days'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for overlapping leave requests
            overlapping_requests = LeaveRequest.objects.filter(
                employee=target_employee,
                status__in=['PENDING', 'APPROVED'],
                start_date__lte=end_date_obj,
                end_date__gte=start_date_obj
            )
            
            if overlapping_requests.exists():
                return Response({
                    'status': False,
                    'message': 'You have overlapping leave requests for the selected dates'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create leave request
            leave_request = LeaveRequest.objects.create(
                employee=target_employee,
                start_date=start_date_obj,
                end_date=end_date_obj,
                reason=reason,
                status='PENDING'
            )
            
            return Response({
                'status': True,
                'message': 'Leave request submitted successfully',
                'data': {
                    'request_id': str(leave_request.id),
                    'employee_name': target_employee.user.name if target_employee.user else 'Unknown',
                    'start_date': leave_request.start_date.strftime('%Y-%m-%d'),
                    'end_date': leave_request.end_date.strftime('%Y-%m-%d'),
                    'days_requested': days_requested,
                    'reason': leave_request.reason,
                    'status': leave_request.status,
                    'current_balance': current_balance,
                    'balance_after_approval': current_balance - days_requested,
                    'applied_by': user.name,
                    'applied_for': target_employee.user.name if target_employee.user else 'Unknown'
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error submitting leave request',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ApproveRejectLeave(APIView):
    """
    Function 3: Single function for HR and MANAGER to Approve or Reject leave
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Check permissions
            if user.role not in ['HR', 'MANAGER']:
                return Response({
                    'status': False,
                    'message': 'Only HR and MANAGER can approve/reject leave requests'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get request data
            request_id = request.data.get('request_id')
            action = request.data.get('action', '').upper()
            comments = request.data.get('comments', '')
            
            if not request_id:
                return Response({
                    'status': False,
                    'message': 'request_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if action not in ['APPROVED', 'REJECTED']:
                return Response({
                    'status': False,
                    'message': 'action must be either APPROVED or REJECTED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get leave request
            leave_request = LeaveRequest.objects.filter(id=request_id).first()
            if not leave_request:
                return Response({
                    'status': False,
                    'message': 'Leave request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if request is still pending
            if leave_request.status != 'PENDING':
                return Response({
                    'status': False,
                    'message': f'Cannot modify leave request. Current status: {leave_request.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # For MANAGER: verify permission to approve this request
            if user.role == 'MANAGER':
                manager_employee = Employee.objects.filter(user=user).first()
                if not manager_employee:
                    return Response({
                        'status': False,
                        'message': 'Manager employee record not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Check if employee is in manager's team
                managed_projects = Project.objects.filter(manager=manager_employee)
                team_members = TeamMembersMapping.objects.filter(
                    team__project_id__in=managed_projects
                ).values_list('user_id', flat=True)
                
                is_team_member = (
                    leave_request.employee.user_id in team_members or
                    managed_projects.filter(resource=leave_request.employee).exists()
                )
                
                if not is_team_member:
                    return Response({
                        'status': False,
                        'message': 'You can only approve/reject leave requests from your team members'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Calculate days
            days_requested = (leave_request.end_date - leave_request.start_date).days + 1
            
            # Get current leave balance
            try:
                leave_balance_obj = LeaveBalance.objects.get(employee=leave_request.employee)
                current_balance = leave_balance_obj.balance
            except LeaveBalance.DoesNotExist:
                leave_balance_obj = LeaveBalance.objects.create(
                    employee=leave_request.employee,
                    balance=24
                )
                current_balance = 24
            
            # Update leave request
            leave_request.status = action
            
            # Add approval tracking if fields exist
            if hasattr(leave_request, 'approved_by'):
                leave_request.approved_by = user
            if hasattr(leave_request, 'comments'):
                leave_request.comments = comments
            if hasattr(leave_request, 'approved_at'):
                leave_request.approved_at = timezone.now()
            
            leave_request.save()
            
            # Update leave balance if approved
            balance_updated = False
            if action == 'APPROVED':
                if current_balance >= days_requested:
                    leave_balance_obj.balance -= days_requested
                    leave_balance_obj.save()
                    balance_updated = True
                    new_balance = leave_balance_obj.balance
                else:
                    new_balance = current_balance
            else:
                new_balance = current_balance
            
            return Response({
                'status': True,
                'message': f'Leave request {action.lower()} successfully',
                'data': {
                    'request_id': str(leave_request.id),
                    'employee_name': leave_request.employee.user.name if leave_request.employee.user else 'Unknown',
                    'employee_email': leave_request.employee.user.email if leave_request.employee.user else None,
                    'start_date': leave_request.start_date.strftime('%Y-%m-%d'),
                    'end_date': leave_request.end_date.strftime('%Y-%m-%d'),
                    'days_requested': days_requested,
                    'status': leave_request.status,
                    'action_by': user.name,
                    'comments': comments,
                    'leave_balance': {
                        'previous_balance': current_balance,
                        'current_balance': new_balance,
                        'balance_updated': balance_updated
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error processing leave action',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserLeaveBalance(APIView):
    """
    Function 4: Show leave balance of current logged in user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Get employee record for current user
            employee = Employee.objects.filter(user=user).first()
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found for current user'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get leave balance
            try:
                leave_balance_obj = LeaveBalance.objects.get(employee=employee)
                current_balance = leave_balance_obj.balance
            except LeaveBalance.DoesNotExist:
                # Create default balance
                leave_balance_obj = LeaveBalance.objects.create(
                    employee=employee,
                    balance=24
                )
                current_balance = 24
            
            # Get leave statistics
            current_year = timezone.now().year
            
            # Total leave requests this year
            total_requests = LeaveRequest.objects.filter(
                employee=employee,
                start_date__year=current_year
            )
            
            # Calculate used days (approved requests)
            approved_requests = total_requests.filter(status='APPROVED')
            used_days = sum([
                (req.end_date - req.start_date).days + 1 
                for req in approved_requests
            ])
            
            # Pending requests
            pending_requests = total_requests.filter(status='PENDING')
            pending_days = sum([
                (req.end_date - req.start_date).days + 1 
                for req in pending_requests
            ])
            
            return Response({
                'status': True,
                'message': 'Leave balance retrieved successfully',
                'data': {
                    'employee_info': {
                        'id': str(employee.id),
                        'name': user.name,
                        'email': user.email,
                        'designation': employee.designation,
                        'department': employee.department.name if employee.department else None
                    },
                    'leave_balance': {
                        'current_balance': current_balance,
                        'total_allocated': 24,  # Default allocation
                        'used_days': used_days,
                        'pending_days': pending_days,
                        'available_days': current_balance
                    },
                    'statistics': {
                        'total_requests_this_year': total_requests.count(),
                        'approved_requests': approved_requests.count(),
                        'rejected_requests': total_requests.filter(status='REJECTED').count(),
                        'pending_requests': pending_requests.count()
                    },
                    'year': current_year
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching leave balance',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EmployeeLeaveBalance(APIView):
    """
    Function 5: Show leave balance to HR/MANAGER for specific employee (for approval decisions)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Check permissions
            if user.role not in ['HR', 'MANAGER']:
                return Response({
                    'status': False,
                    'message': 'Only HR and MANAGER can view employee leave balances'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get employee ID
            employee_id = request.data.get('employee_id')
            if not employee_id:
                return Response({
                    'status': False,
                    'message': 'employee_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get target employee
            target_employee = Employee.objects.filter(id=employee_id).first()
            if not target_employee:
                return Response({
                    'status': False,
                    'message': 'Employee not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # For MANAGER: verify employee is in their team
            if user.role == 'MANAGER':
                manager_employee = Employee.objects.filter(user=user).first()
                if not manager_employee:
                    return Response({
                        'status': False,
                        'message': 'Manager employee record not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                managed_projects = Project.objects.filter(manager=manager_employee)
                team_members = TeamMembersMapping.objects.filter(
                    team__project_id__in=managed_projects
                ).values_list('user_id', flat=True)
                
                is_team_member = (
                    target_employee.user_id in team_members or
                    managed_projects.filter(resource=target_employee).exists()
                )
                
                if not is_team_member:
                    return Response({
                        'status': False,
                        'message': 'You can only view leave balance for your team members'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Get leave balance
            try:
                leave_balance_obj = LeaveBalance.objects.get(employee=target_employee)
                current_balance = leave_balance_obj.balance
            except LeaveBalance.DoesNotExist:
                current_balance = 24  # Default
            
            # Get leave statistics
            current_year = timezone.now().year
            
            # Total leave requests this year
            total_requests = LeaveRequest.objects.filter(
                employee=target_employee,
                start_date__year=current_year
            )
            
            # Calculate used days (approved requests)
            approved_requests = total_requests.filter(status='APPROVED')
            used_days = sum([
                (req.end_date - req.start_date).days + 1 
                for req in approved_requests
            ])
            
            # Pending requests
            pending_requests = total_requests.filter(status='PENDING')
            pending_days = sum([
                (req.end_date - req.start_date).days + 1 
                for req in pending_requests
            ])
            
            # Recent leave requests
            recent_requests = total_requests.order_by('-created_at')[:5]
            recent_requests_data = []
            
            for req in recent_requests:
                days = (req.end_date - req.start_date).days + 1
                recent_requests_data.append({
                    'id': str(req.id),
                    'start_date': req.start_date.strftime('%Y-%m-%d'),
                    'end_date': req.end_date.strftime('%Y-%m-%d'),
                    'days': days,
                    'reason': req.reason,
                    'status': req.status,
                    'applied_on': req.created_at.strftime('%Y-%m-%d')
                })
            
            return Response({
                'status': True,
                'message': 'Employee leave balance retrieved successfully',
                'data': {
                    'employee_info': {
                        'id': str(target_employee.id),
                        'name': target_employee.user.name if target_employee.user else 'Unknown',
                        'email': target_employee.user.email if target_employee.user else None,
                        'designation': target_employee.designation,
                        'department': target_employee.department.name if target_employee.department else None
                    },
                    'leave_balance': {
                        'current_balance': current_balance,
                        'total_allocated': 24,
                        'used_days': used_days,
                        'pending_days': pending_days,
                        'available_days': current_balance
                    },
                    'statistics': {
                        'total_requests_this_year': total_requests.count(),
                        'approved_requests': approved_requests.count(),
                        'rejected_requests': total_requests.filter(status='REJECTED').count(),
                        'pending_requests': pending_requests.count()
                    },
                    'recent_requests': recent_requests_data,
                    'year': current_year,
                    'requested_by': {
                        'role': user.role,
                        'name': user.name
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching employee leave balance',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



# Add this to hr_management_views.py at the end

class HRDashboardMetrics(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.role != 'HR':
            return Response({
                'status': False,
                'message': 'Only HR can access dashboard metrics'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            department_name = request.query_params.get('department', '')
            time_range = request.query_params.get('timeRange', 'year')
            employee_qs = Employee.objects.all()
            leave_qs = LeaveRequest.objects.all()
            attendance_qs = Attendance.objects.all()

            # Apply time range filter
            current_date = timezone.now()
            if time_range == 'month':
                start_date = current_date - timedelta(days=30)
                employee_qs = employee_qs.filter(date_of_joining__gte=start_date)
                leave_qs = leave_qs.filter(start_date__gte=start_date)
                attendance_qs = attendance_qs.filter(date__gte=start_date)
            elif time_range == 'year':
                start_date = current_date - timedelta(days=365)
                employee_qs = employee_qs.filter(date_of_joining__gte=start_date)
                leave_qs = leave_qs.filter(start_date__gte=start_date)
                attendance_qs = attendance_qs.filter(date__gte=start_date)

            if department_name:
                department = Department.objects.filter(name=department_name).first()
                if not department:
                    return Response({'status': False, 'message': 'Department not found'}, status=400)
                employee_qs = employee_qs.filter(department=department)
                leave_qs = leave_qs.filter(employee__department=department)
                attendance_qs = attendance_qs.filter(employee__department=department)

            # Total employees
            total_employees = employee_qs.count()

            # New hires
            current_month = current_date.month
            current_year = current_date.year
            new_hires = employee_qs.filter(date_of_joining__month=current_month, date_of_joining__year=current_year).count()

            # Pending leaves
            pending_leaves = leave_qs.filter(status='PENDING').count()

            # Total and average salary
            salaries = []
            for emp in employee_qs:
                try:
                    sal = float(emp.salary)
                    salaries.append(sal)
                except ValueError:
                    pass
            total_salary = sum(salaries)
            avg_salary = total_salary / len(salaries) if salaries else 0

            # Department count
            dept_qs = Department.objects.all()
            if department_name:
                dept_qs = dept_qs.filter(name=department_name)
            dept_count = dept_qs.count()

            # Bar heights - employees per department
            bar_heights = []
            max_emp = 1
            for d in Department.objects.all():
                count = Employee.objects.filter(department=d).count()
                bar_heights.append(count)
                if count > max_emp:
                    max_emp = count
            bar_heights = [round((c / max_emp * 100), 1) if max_emp > 0 else 0 for c in bar_heights]

            # Line points - employees joined per month
            line_points = []
            months = 12 if time_range == 'year' else 1 if time_range == 'month' else 24
            for m in range(1, months + 1):
                month_date = current_date - timedelta(days=30 * (12 - m)) if time_range == 'year' else current_date
                count = Employee.objects.filter(date_of_joining__month=month_date.month, date_of_joining__year=month_date.year).count()
                y = 50 - count * 5  # Arbitrary scaling for SVG
                line_points.append(y)
            line_str = ''
            for i, y in enumerate(line_points):
                x = 10 + i * (180 / (months - 1)) if months > 1 else 10
                line_str += f"{round(x)},{round(y)} "
            line_points_str = line_str.strip()

            # Pie dasharray - approved leaves percentage
            total_leaves = leave_qs.count()
            approved = leave_qs.filter(status='APPROVED').count()
            approved_perc = round((approved / total_leaves * 100), 1) if total_leaves > 0 else 0
            pie_dasharray = f"{approved_perc} {100 - approved_perc}"

            # Company stats - per department
            stats = []
            for d in dept_qs:
                emps = employee_qs.filter(department=d)
                emp_count = emps.count()
                dept_salaries = []
                for e in emps:
                    try:
                        dept_salaries.append(float(e.salary))
                    except:
                        pass
                dept_avg_salary = sum(dept_salaries) / len(dept_salaries) if dept_salaries else 0
                stats.append({
                    "label": d.name,
                    "primary": round(dept_avg_salary),
                    "secondary": emp_count
                })

            # Donuts - attendance rate, leave rate
            current_date = timezone.now().date()
            attendance_today = attendance_qs.filter(date=current_date).count()
            attendance_rate = round((attendance_today / total_employees * 100), 1) if total_employees > 0 else 0
            leave_rate = round((pending_leaves / total_employees * 100), 1) if total_employees > 0 else 0

            # Turnover rate (simulated as percentage of employees with end_date)
            turnover_data = []
            for m in range(1, 7):  # Last 6 months for turnover
                month_date = current_date - timedelta(days=30 * (6 - m))
                terminated = Employee.objects.filter(end_date__month=month_date.month, end_date__year=month_date.year).count()
                total = Employee.objects.filter(date_of_joining__lte=month_date).count()
                rate = round((terminated / total * 100), 1) if total > 0 else 0
                turnover_data.append({"month": month_date.strftime('%b'), "rate": rate})

            # Title and filters
            company_name = Employee.objects.first().company.name if Employee.objects.exists() else 'HR Dashboard'
            filter_options = list(Department.objects.values_list('name', flat=True))

            data = {
                "title": company_name,
                "filter_options": filter_options,
                "economics": {
                    "cost": round(total_salary),
                    "revenue": round(avg_salary),
                    "orders": total_employees,
                    "profit": new_hires,
                    "returns": pending_leaves
                },
                "diversity": {
                    "value": dept_count,
                    "bar_heights": bar_heights
                },
                "website": {
                    "line_points": line_points_str
                },
                "employee": {
                    "pie_dasharray": pie_dasharray
                },
                "company": {
                    "stats": stats,
                    "donuts": [attendance_rate, leave_rate]
                },
                "turnover": turnover_data
            }

            return Response({
                'status': True,
                'message': 'Dashboard metrics retrieved successfully',
                'data': data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching dashboard metrics',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)