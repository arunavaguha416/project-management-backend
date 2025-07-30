# department/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from ..models.department_model import Department
from ..serializers.department_serializers import DepartmentSerializer
from django.core.paginator import Paginator
import datetime

# API to add a new department (admin-only)
class DepartmentAdd(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            serializer = DepartmentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Department added successfully',
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
                'message': 'An error occurred while adding the department',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# API to list departments with optional search and pagination (authenticated users)
class DepartmentList(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try: 
            query = Q()  
            departments = Department.objects.filter(query).order_by('-created_at')

            if departments.exists():                    
                serializer = DepartmentSerializer(departments, many=True)
                return Response({
                    'status': True,
                    'count': departments.count(),
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Departments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# API to list soft-deleted departments (admin-only)
class DeletedDepartmentList(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')

            query = Q(deleted_at__isnull=False)
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)

            departments = Department.all_objects.filter(query).order_by('-created_at')

            if departments.exists():
                if page is not None:
                    paginator = Paginator(departments, page_size)
                    paginated_departments = paginator.get_page(page)
                    serializer = DepartmentSerializer(paginated_departments, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = DepartmentSerializer(departments, many=True)
                    return Response({
                        'status': True,
                        'count': departments.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted departments not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# API to retrieve department details (authenticated users)
class DepartmentDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            department_id = request.data.get('id')
            if department_id:
                department = Department.objects.filter(id=department_id).values(
                    'id', 'name', 'description', 'manager', 'published_at'
                ).first()
                if department:
                    return Response({
                        'status': True,
                        'records': department
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Department not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide departmentId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching department details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# API to update a department (admin-only)
class DepartmentUpdate(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            department_id = request.data.get('id')
            department = Department.objects.filter(id=department_id).first()
            if department:
                if not department.deleted_at:
                    serializer = DepartmentSerializer(department, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({
                            'status': True,
                            'message': 'Department updated successfully'
                        }, status=status.HTTP_200_OK)
                    return Response({
                        'status': False,
                        'message': 'Invalid data',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'status': False,
                        'message': 'Cannot update a deleted department'
                    }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Department not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the department',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# API to soft delete a department (admin-only)
class DepartmentDelete(APIView):
    permission_classes = (IsAdminUser,)

    def delete(self, request, department_id):
        try:
            department = Department.objects.filter(id=department_id).first()
            if department:
                if not department.deleted_at:
                    department.soft_delete()
                    return Response({
                        'status': True,
                        'message': 'Department deleted successfully'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Department is already deleted'
                    }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Department not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# API to restore a soft-deleted department (admin-only)
class RestoreDepartment(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            department_id = request.data.get('id')
            department = Department.all_objects.filter(id=department_id).first()
            if department:
                if department.deleted_at:
                    department.deleted_at = None
                    department.save()
                    return Response({
                        'status': True,
                        'message': 'Department restored successfully'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Department is not deleted'
                    }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Department not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)