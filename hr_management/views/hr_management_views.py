from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from hr_management.models.hr_management_models import Employee, LeaveRequest
from hr_management.serializers.hr_management_serializer import EmployeeSerializer, LeaveRequestSerializer
from django.core.paginator import Paginator
import datetime

# Employee Views
class EmployeeAdd(APIView):
    permission_classes = (IsAdminUser,)

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
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)    
            search_department = search_data.get('department', '')

            query = Q()
            if search_department:
                query &= Q(department__icontains=search_department)

            employees = Employee.objects.filter(query).order_by('-created_at')

            if employees.exists():
                if page is not None:
                    paginator = Paginator(employees, page_size)
                    paginated_employees = paginator.get_page(page)
                    serializer = EmployeeSerializer(paginated_employees, many=True)
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
                    'message': 'Employees not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PublishedEmployeeList(APIView):
    permission_classes= (AllowAny,)

    def get(self, request):
        try:
            employees = Employee.objects.filter(published_at__isnull=False).values('id', 'user.username').order_by('-created_at')
            if employees.exists():
                return Response({
                    'status': True,
                    'records': employees
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Employees not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_REQUEST)

class DeletedEmployeeList(APIView):
    permission_classes=(IsAdminUser,)

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
    permission_classes = (IsAdminUser,)

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
    permission_classes = (IsAdminUser,)

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

class ChangeEmployeePublishStatus(APIView):
    permission_classes = [IsAdminUser,]

    def put(self, request):
        try:
            employee_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            employee = Employee.objects.get(id=employee_id)
            serializer = EmployeeSerializer(employee, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Publish status updated successfully',
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Unable to update publish status',
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

class EmployeeDelete(APIView):
    permission_classes = [IsAdminUser,]

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
    permission_classes = [IsAdminUser,]

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
    permission_classes = (IsAdminUser,)

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

class PublishedLeaveRequestList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            leave_requests = LeaveRequest.objects.filter(published_at__isnull=False).values('id', 'reason').order_by('-created_at')
            if leave_requests.exists():
                return Response({
                    'status': True,
                    'records': leave_requests
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

class DeletedLeaveRequestList(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_reason = search_data.get('reason', '')

            query = Q(deleted_at__isnull=False)
            if search_reason:
                query &= Q(reason__icontains=search_reason)

            leave_requests = LeaveRequest.all_objects.filter(query).order_by('-created_at')

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
                    'message': 'Deleted leave requests not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestDetails(APIView):
    permission_classes = (IsAdminUser,)

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
    permission_classes = (IsAdminUser,)

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

class ChangeLeaveRequestPublishStatus(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            leave_request_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            serializer = LeaveRequestSerializer(leave_request, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Publish status updated successfully',
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Unable to update publish status',
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

class LeaveRequestDelete(APIView):
    permission_classes = (IsAdminUser,)

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
    permission_classes = (IsAdminUser,)

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
