from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from hr_management.models.hr_management_models import Employee, LeaveRequest
from hr_management.serializers.hr_management_serializer import EmployeeSerializer, LeaveRequestSerializer, AttendanceSerializer
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

# LeaveRequest Views
class LeaveRequestAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            serializer = LeaveRequestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Leave request added successfully',
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
                'message': 'An error occurred while adding the leave request',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_reason = search_data.get('reason', '')

            query = Q()
            if search_reason:
                query &= Q(reason__icontains=search_reason)

            leave_requests = LeaveRequest.objects.filter(query).order_by('-created_at')

            if leave_requests.exists():
                if page is not None:
                    paginator = Paginator(leave_requests, page_size)
                    paginated_requests = paginator.get_page(page)
                    serializer = LeaveRequestSerializer(paginated_requests, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = LeaveRequestSerializer(leave_requests, many=True)
                    return Response({
                        'status': True,
                        'count': leave_requests.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Leave requests not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            leave_request_id = request.data.get('id')
            if leave_request_id:
                leave_request = LeaveRequest.objects.filter(id=leave_request_id).values(
                    'id', 'employee__user__username', 'start_date', 'end_date', 'reason', 'status'
                ).first()
                if leave_request:
                    return Response({
                        'status': True,
                        'records': leave_request
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Leave request not found',
                    }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Please provide leaveRequestId'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching leave request details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            leave_request_id = request.data.get('id')
            leave_request = LeaveRequest.objects.filter(id=leave_request_id).first()
            if leave_request:
                serializer = LeaveRequestSerializer(leave_request, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Leave request updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Leave request not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the leave request',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, leave_request_id):
        try:
            leave_request = LeaveRequest.objects.filter(id=leave_request_id).first()
            if leave_request:
                leave_request.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Leave request deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Leave request not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreLeaveRequest(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            leave_request_id = request.data.get('id')
            leave_request = LeaveRequest.all_objects.get(id=leave_request_id)
            if leave_request:
                leave_request.deleted_at = None
                leave_request.save()
                return Response({
                    'status': True,
                    'message': 'Leave request restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Leave request not found'
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


# --- 6. Leave Request Update ---
class LeaveRequestUpdate(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        leave_id = request.data.get('id')
        new_status = request.data.get('status', '').upper()
        leave = LeaveRequest.objects.get(id=leave_id)
        if new_status in ['APPROVED', 'REJECTED']:
            leave.status = new_status
            leave.save()
            return Response({'status': True, 'msg': 'Leave updated'})
        return Response({'status': False, 'msg': 'Invalid status'}, status=400)
    
    
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

        
class EmployeeLeaveRequestList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get request parameters
            employee_id = request.data.get('employee_id')
            page_size = request.data.get('page_size', 10)
            search = request.data.get('search', '').strip()
            status_filter = request.data.get('status', '').strip()
            date_from = request.data.get('date_from')
            date_to = request.data.get('date_to')
            
            # Build base query
            query = Q()
            
            # If specific employee_id is provided, filter by that employee
            if employee_id:
                user = User.objects.filter(id=employee_id).first()
                if not user:
                    return Response({
                        'status': False,
                        'message': 'User not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                employee = Employee.objects.filter(user=user).first()
                if not employee:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                query &= Q(employee=employee)
            
            # Permission check - regular employees can only see their own leave requests
            if request.user.role not in ['HR', 'ADMIN', 'MANAGER']:
                user_employee = Employee.objects.filter(user=request.user).first()
                if user_employee:
                    query &= Q(employee=user_employee)
                else:
                    return Response({
                        'status': False,
                        'message': 'Employee record not found for current user'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # Apply search filter
            if search:
                query &= (
                    Q(employee__user__name__icontains=search) |
                    Q(reason__icontains=search) |
                    Q(status__icontains=search)
                )
            
            # Apply status filter
            if status_filter:
                query &= Q(status__iexact=status_filter)
            
            # Apply date range filters
            if date_from:
                query &= Q(start_date__gte=date_from)
            if date_to:
                query &= Q(end_date__lte=date_to)
            
            # Get leave requests with related data
            leaves = LeaveRequest.objects.select_related(
                'employee__user', 
                'employee__department',
                'employee__company'
            ).filter(query).order_by('-created_at')
            
            # Apply pagination
            if page_size:
                leaves = leaves[:int(page_size)]
            
            # Build response data
            leave_data = []
            stats = {
                'total_requests': 0,
                'approved': 0,
                'rejected': 0,
                'pending': 0,
                'total_days_requested': 0,
                'total_days_approved': 0
            }
            
            for leave in leaves:
                # Calculate days requested
                days_requested = 0
                if leave.start_date and leave.end_date:
                    days_requested = (leave.end_date - leave.start_date).days + 1
                
                leave_data.append({
                    'id': str(leave.id),
                    'employee_id': str(leave.employee.id),
                    'employee_name': leave.employee.user.name if leave.employee.user else 'Unknown',
                    'employee_email': leave.employee.user.email if leave.employee.user else None,
                    'designation': leave.employee.designation,
                    'department': leave.employee.department.name if leave.employee.department else None,
                    'start_date': leave.start_date.strftime('%Y-%m-%d') if leave.start_date else None,
                    'end_date': leave.end_date.strftime('%Y-%m-%d') if leave.end_date else None,
                    'days_requested': days_requested,
                    'reason': leave.reason,
                    'status': leave.status,
                    'applied_on': leave.created_at.strftime('%Y-%m-%d %H:%M:%S') if leave.created_at else None,
                    'approved_by': leave.approved_by.name if hasattr(leave, 'approved_by') and leave.approved_by else None,
                    'comments': getattr(leave, 'comments', None)
                })
                
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
                'count': len(leave_data),
                'records': leave_data,
                'stats': stats,
                'filters': {
                    'employee_id': employee_id,
                    'search': search,
                    'status': status_filter,
                    'date_from': date_from,
                    'date_to': date_to,
                    'page_size': page_size
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching leave requests',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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

        



class ManagerLeaveRequests(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # This is a placeholder implementation
            # Replace with actual leave management logic when available
            
            return Response({
                'status': True,
                'count': 0,
                'records': [],
                'message': 'Leave management system not yet implemented'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching leave requests',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ManagerLeaveAction(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Placeholder for leave approval/rejection
            return Response({
                'status': True,
                'message': 'Leave management system not yet implemented'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error processing leave action',
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


 


