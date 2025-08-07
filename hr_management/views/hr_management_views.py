from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from hr_management.models.hr_management_models import Employee, LeaveRequest
from hr_management.serializers.hr_management_serializer import EmployeeSerializer, LeaveRequestSerializer, AttendanceSerializer
from django.core.paginator import Paginator
from datetime import timedelta

from django.utils import timezone
from projects.models.project_model import Project
from authentication.models.user import User
from hr_management.models.hr_management_models import Attendance

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
                    
                )

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
    def get(self, request, id):
        try:
            employee = Employee.objects.filter(id=id).first()
            if not employee:
                return Response({'status': False, 'message': 'Employee not found'}, status=404)
            attendances = Attendance.objects.filter(employee=employee).order_by('-date')
            serializer = AttendanceSerializer(attendances, many=True)
            return Response({'status': True, 'records': serializer.data})
        except Exception as e:
            return Response({'status': False, 'error': str(e)}, status=400)
        
class EmployeeLeaveRequestList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        leaves = LeaveRequest.objects.order_by('-created_at')
        serializer = LeaveRequestSerializer(leaves, many=True)
        return Response({'records': serializer.data})
