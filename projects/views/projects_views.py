from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from projects.models.project_model import *
from projects.serializers.project_serializer import ProjectSerializer
from django.core.paginator import Paginator
import datetime
from projects.models.task_model import Task
from hr_management.models.hr_management_models import Employee
from authentication.models.user import User
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import UploadedFile
from projects.models.project_model import *

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename

from datetime import datetime
import os

class ProjectAdd(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        try:
            data = request.data.copy()
            
            # Validate manager_id if provided
            manager = None
            manager_id = data.get('manager_id')
            if manager_id and manager_id.strip():  # Check if not empty
                manager = Employee.objects.filter(id=manager_id).first()
                if not manager:
                    return Response({
                        'status': False,
                        'message': f'Manager with ID {manager_id} not found in employee records'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create project with validated objects (only fields that exist in your model)
            project = Project.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                manager=manager,  # Use manager object, not manager_id
                # Note: No owner or company fields as they don't exist in your current model
            )
            
            # Create response data based on actual model fields
            project_data = {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'manager_id': str(project.manager.id) if project.manager else None,
                'manager_name': project.manager.user.name if project.manager and project.manager.user else None,
                'status': project.status,
                'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return Response({
                'status': True,
                'message': 'Project added successfully',
                'records': project_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while adding the project',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_project = search_data.get('search', '').strip()

            # Build query with proper joins to avoid N+1 queries
            projects_queryset = Project.objects.select_related('manager__user').all()

            # Apply search filters
            query = Q()
            if search_project:
                query &= (
                    Q(name__icontains=search_project) |
                    Q(description__icontains=search_project) |                    
                    Q(manager__user__name__icontains=search_project) |  # Search by manager's name from User table
                    Q(manager__user__email__icontains=search_project)   # Optional: also search by manager's email
                )

            projects = projects_queryset.filter(query).order_by('-created_at')

            if projects.exists():
                paginator = Paginator(projects, page_size)
                try:
                    paginated_projects = paginator.page(page)
                except Exception:
                    paginated_projects = paginator.page(1)
                
                # Create response data with manager name from User table
                project_data = []
                for project in paginated_projects:
                    project_info = {
                        'id': str(project.id),
                        'name': project.name,
                        'description': project.description,
                        'status': project.status,
                        'manager': {
                            'id': str(project.manager.id) if project.manager else None,
                            'user_id': str(project.manager.user.id) if project.manager and project.manager.user else None,
                            'name': project.manager.user.name if project.manager and project.manager.user else None,
                            'email': project.manager.user.email if project.manager and project.manager.user else None,
                            'username': project.manager.user.username if project.manager and project.manager.user else None
                        } if project.manager else None,
                        'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    project_data.append(project_info)
                
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': project_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Projects not found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DeletedProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')
            company_id = search_data.get('company_id', '')

            query = Q(deleted_at__isnull=False)
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)
            if company_id:
                query &= Q(company__id=company_id)

            projects = Project.all_objects.filter(query).order_by('-created_at')

            if projects.exists():
                if page is not None:
                    paginator = Paginator(projects, page_size)
                    paginated_projects = paginator.get_page(page)
                    serializer = ProjectSerializer(paginated_projects, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = ProjectSerializer(projects, many=True)
                    return Response({
                        'status': True,
                        'count': projects.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted projects not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ProjectDetails(APIView):
    def get(self, request, id):
        try:
            # Remove 'client' from select_related since it's not a valid field
            project = Project.objects.select_related('manager').filter(id=id).first()
            if not project:
                return Response({'status': False, 'message': 'Not found'}, status=404)
            
            data = {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'manager_name': project.manager.user.name if project.manager else None,
                'manager_id': project.manager.user.id if project.manager else None,
                'start_date': project.start_date,
                'end_date': project.end_date,
                'status': project.status,
                'client_name': getattr(project, 'client_name', None),  # Use direct field if available
                'current_sprint': getattr(project, 'current_sprint', None),
            }
            
            # Fetch tasks separately if needed
            tasks = Task.objects.filter(project=project)
            task_data = [{
                'id': t.id, 
                'title': t.title, 
                'assigned_to_name': t.assigned_to.name if t.assigned_to else None, 
                'status': t.status
            } for t in tasks]

            return Response({'status': True, 'records': data, 'tasks': task_data})

        except Exception as e:
            return Response({'status': False, 'error': str(e)}, status=400)

class ProjectUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            project_id = request.data.get('id')
            project = Project.objects.filter(id=project_id).first()
            if project:
                serializer = ProjectSerializer(project, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Project updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Project not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the project',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ProjectDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, project_id):
        try:
            project = Project.objects.filter(id=project_id).first()
            if project:
                project.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Project deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreProject(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('id')
            project = Project.all_objects.get(id=project_id)
            if project:
                project.deleted_at = None
                project.save()
                return Response({
                    'status': True,
                    'message': 'Project restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        

class ProjectSummary(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        search = request.data.get('search', '').strip()
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 5))
        qs = Project.objects.filter(deleted_at__isnull=True)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(team_name__icontains=search) |
                Q(manager__name__icontains=search)
            )
        total = qs.count()
        qs = qs.order_by('-created_at')[(page-1)*page_size : page*page_size]
        serializer = ProjectSerializer(qs, many=True)
        return Response({'records': serializer.data, 'count': total})
    
class ManagerProjects(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            employee = Employee.objects.filter(user=user).first()
            
            if not employee:
                return Response({
                    'status': False,
                    'message': 'Employee record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_term = search_data.get('search', '').strip()
            
            # Get projects managed by this manager
            projects_query = Project.objects.filter(manager=employee).select_related('manager__user')
            
            # Apply search filter
            if search_term:
                projects_query = projects_query.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
            
            projects = projects_query.order_by('-created_at')
            
            if projects.exists():
                paginator = Paginator(projects, page_size)
                try:
                    paginated_projects = paginator.page(page)
                except:
                    paginated_projects = paginator.page(1)
                
                project_data = []
                for project in paginated_projects:
                    # Get team size for this project
                    team_size = UserMapping.objects.filter(project=project).count()
                    
                    # Calculate progress (placeholder - you might have actual progress tracking)
                    progress = 50 if project.status == 'Ongoing' else 100 if project.status == 'Completed' else 0
                    
                    project_info = {
                        'id': str(project.id),
                        'name': project.name,
                        'description': project.description,
                        'status': project.status,
                        'team_size': team_size,
                        'progress': progress,
                        'deadline': None,  # Add deadline field to your Project model if needed
                        'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    project_data.append(project_info)
                
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'current_page': page,
                    'records': project_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'No projects found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching managed projects',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AssignProjectManager(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        try:
            # Get data from request
            project_id = request.data.get('id')
            manager_id = request.data.get('manager_id')
            
            # Validate required fields
            if not project_id or not manager_id:
                return Response({
                    'status': False,
                    'message': 'Project ID and Manager ID are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check user permissions (only HR and ADMIN can assign managers)
            if request.user.role not in ['HR', 'ADMIN']:
                return Response({
                    'status': False,
                    'message': 'Insufficient permissions to assign project manager'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get project
            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get manager employee record
            manager_employee = Employee.objects.filter(
                id=manager_id, 
                user__role='MANAGER'
            ).first()
            
            if not manager_employee:
                return Response({
                    'status': False,
                    'message': 'Manager not found or user is not a manager'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if project is in assignable status
            if project.status not in ['Ongoing', 'PENDING']:
                return Response({
                    'status': False,
                    'message': 'Can only assign managers to ongoing or pending projects'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update project manager
            project.manager = manager_employee
            project.save()
            
            return Response({
                'status': True,
                'message': 'Project manager assigned successfully',
                'records': {
                    'project_id': project.id,
                    'project_name': project.name,
                    'manager_id': manager_employee.id,
                    'manager_name': manager_employee.user.name if manager_employee.user else 'Unknown'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while assigning project manager',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EmployeeProjectList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get request parameters
            employee_id = request.data.get('employee_id')
            page_size = request.data.get('page_size', 10)
            search = request.data.get('search', '').strip()
            status_filter = request.data.get('status', '').strip()
            
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
            
            # Permission check - regular employees can only see their own projects
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
                    Q(project__name__icontains=search) |
                    Q(project__description__icontains=search) |
                    Q(employee__user__name__icontains=search)
                )
            
            # Apply status filter
            if status_filter:
                query &= Q(project__status__iexact=status_filter)
            
            # Get project assignments using UserMapping
            user_mappings = UserMapping.objects.select_related(
                'project',
                'employee__user',
                'employee__department',
                'employee__company'
            ).filter(query).order_by('-created_at')
            
            # Apply pagination
            if page_size:
                user_mappings = user_mappings[:int(page_size)]
            
            # Build response data
            projects_data = []
            stats = {
                'total_projects': 0,
                'ongoing_projects': 0,
                'completed_projects': 0,
                'pending_projects': 0
            }
            
            for mapping in user_mappings:
                project = mapping.project
                employee = mapping.employee
                
                # Get project manager info
                manager_info = None
                manager_mapping = ManagerMapping.objects.select_related('manager__user').filter(project=project).first()
                if manager_mapping and manager_mapping.manager:
                    manager_info = {
                        'id': str(manager_mapping.manager.id),
                        'name': manager_mapping.manager.user.name if manager_mapping.manager.user else 'Unknown'
                    }
                
                projects_data.append({
                    'mapping_id': str(mapping.id),
                    'project_id': str(project.id),
                    'project_name': project.name,
                    'project_description': project.description,
                    'project_status': project.status,
                    'employee_id': str(employee.id),
                    'employee_name': employee.user.name if employee.user else 'Unknown',
                    'employee_email': employee.user.email if employee.user else None,
                    'designation': employee.designation,
                    'department': employee.department.name if employee.department else None,
                    'company': employee.company.name if employee.company else None,
                    'manager': manager_info,
                    'assigned_date': mapping.created_at.strftime('%Y-%m-%d') if mapping.created_at else None,
                    'project_created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else None,
                    'project_updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S') if project.updated_at else None
                })
                
                # Update statistics
                stats['total_projects'] += 1
                
                if project.status == 'Ongoing':
                    stats['ongoing_projects'] += 1
                elif project.status == 'Completed':
                    stats['completed_projects'] += 1
                else:
                    stats['pending_projects'] += 1
            
            return Response({
                'status': True,
                'message': 'Employee projects retrieved successfully',
                'count': len(projects_data),
                'records': projects_data,
                'stats': stats,
                'filters': {
                    'employee_id': employee_id,
                    'search': search,
                    'status': status_filter,
                    'page_size': page_size
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching employee projects',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectTasksList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            page_size = request.data.get('page_size', 10)
            search = request.data.get('search', '').strip()
            status_filter = request.data.get('status', '').strip()
            
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
            
            # Build query for tasks
            query = Q(project=project)
            
            # Apply search filter
            if search:
                query &= (
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
                # Only add assigned_to search if the field exists
                try:
                    query |= Q(assigned_to__user__name__icontains=search)
                except:
                    pass
            
            # Apply status filter
            if status_filter:
                query &= Q(status__iexact=status_filter)
            
            # Get tasks
            tasks = Task.objects.select_related('project').filter(query).order_by('-created_at')
            
            # Apply pagination
            if page_size:
                tasks = tasks[:int(page_size)]
            
            # Build tasks data
            tasks_data = []
            stats = {
                'total_tasks': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'overdue': 0
            }
            
            # Import datetime utilities at the top
            from datetime import date, datetime
            from django.utils import timezone
            
            for task in tasks:
                # Check if task is overdue - FIX THE DATE COMPARISON
                is_overdue = False
                if hasattr(task, 'due_date') and task.due_date and task.status != 'COMPLETED':
                    # Convert both to the same type for comparison
                    if isinstance(task.due_date, datetime):
                        # If due_date is datetime, compare with today as datetime
                        today = timezone.now().date()
                        task_date = task.due_date.date()
                        is_overdue = task_date < today
                    elif isinstance(task.due_date, date):
                        # If due_date is date, compare with today as date
                        today = date.today()
                        is_overdue = task.due_date < today
                
                # Get assignee name safely
                assignee_name = "Unassigned"
                if hasattr(task, 'assigned_to') and task.assigned_to:
                    if hasattr(task.assigned_to, 'user') and task.assigned_to.user:
                        assignee_name = task.assigned_to.user.name
                    elif hasattr(task.assigned_to, 'name'):
                        assignee_name = task.assigned_to.name
                
                # Format dates safely
                due_date_str = None
                if hasattr(task, 'due_date') and task.due_date:
                    if isinstance(task.due_date, datetime):
                        due_date_str = task.due_date.date().strftime('%Y-%m-%d')
                    else:
                        due_date_str = task.due_date.strftime('%Y-%m-%d')
                
                created_at_str = None
                if hasattr(task, 'created_at') and task.created_at:
                    if isinstance(task.created_at, datetime):
                        created_at_str = task.created_at.strftime('%Y-%m-%d %H:%M:%S')
                
                updated_at_str = None
                if hasattr(task, 'updated_at') and task.updated_at:
                    if isinstance(task.updated_at, datetime):
                        updated_at_str = task.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                
                tasks_data.append({
                    'id': str(task.id),
                    'title': task.title,
                    'name': task.title,
                    'description': getattr(task, 'description', ''),
                    'status': task.status,
                    'priority': getattr(task, 'priority', 'Medium'),
                    'assigned_to_id': str(task.assigned_to.id) if hasattr(task, 'assigned_to') and task.assigned_to else None,
                    'assignee_name': assignee_name,
                    'due_date': due_date_str,
                    'created_at': created_at_str,
                    'updated_at': updated_at_str,
                    'is_overdue': is_overdue
                })
                
                # Update statistics
                stats['total_tasks'] += 1
                if task.status == 'COMPLETED':
                    stats['completed'] += 1
                elif task.status == 'IN_PROGRESS':
                    stats['in_progress'] += 1
                elif task.status == 'PENDING':
                    stats['pending'] += 1
                
                if is_overdue:
                    stats['overdue'] += 1
            
            return Response({
                'status': True,
                'message': 'Project tasks retrieved successfully',
                'count': len(tasks_data),
                'records': tasks_data,
                'stats': stats,
                'project': {
                    'id': str(project.id),
                    'name': project.name,
                    'status': project.status
                },
                'filters': {
                    'search': search,
                    'status': status_filter,
                    'page_size': page_size
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Add more detailed error logging
            import traceback
            print(f"Error in ProjectTasksList: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            
            return Response({
                'status': False,
                'message': 'An error occurred while fetching project tasks',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectMilestonesList(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            page_size = request.data.get('page_size', 10)
            search = request.data.get('search', '').strip()
            status_filter = request.data.get('status', '').strip()
            
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
            
            # Build query for milestones
            query = Q(project=project)
            
            # Apply search filter
            if search:
                query &= (
                    Q(title__icontains=search) |
                    Q(name__icontains=search) |
                    Q(description__icontains=search)
                )
            
            # Apply status filter
            if status_filter:
                query &= Q(status__iexact=status_filter)
            
            # Get milestones with related data
            milestones = Milestone.objects.select_related(
                'project'
            ).filter(query).order_by('target_date', 'due_date')
            
            # Apply pagination
            if page_size:
                milestones = milestones[:int(page_size)]
            
            # Build milestones data
            milestones_data = []
            stats = {
                'total_milestones': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'overdue': 0
            }
            
            for milestone in milestones:
                # Check if milestone is overdue
                is_overdue = False
                milestone_date = milestone.target_date or milestone.due_date
                if milestone_date and milestone.status != 'COMPLETED':
                    from datetime import date
                    is_overdue = milestone_date < date.today()
                
                milestones_data.append({
                    'id': str(milestone.id),
                    'title': milestone.title if hasattr(milestone, 'title') else milestone.name,
                    'name': milestone.name if hasattr(milestone, 'name') else milestone.title,
                    'description': milestone.description,
                    'status': milestone.status,
                    'target_date': milestone.target_date.strftime('%Y-%m-%d') if hasattr(milestone, 'target_date') and milestone.target_date else None,
                    'due_date': milestone.due_date.strftime('%Y-%m-%d') if hasattr(milestone, 'due_date') and milestone.due_date else None,
                    'completion_percentage': getattr(milestone, 'completion_percentage', 0),
                    'created_at': milestone.created_at.strftime('%Y-%m-%d %H:%M:%S') if milestone.created_at else None,
                    'updated_at': milestone.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(milestone, 'updated_at') and milestone.updated_at else None,
                    'is_overdue': is_overdue
                })
                
                # Update statistics
                stats['total_milestones'] += 1
                if milestone.status == 'COMPLETED':
                    stats['completed'] += 1
                elif milestone.status == 'IN_PROGRESS':
                    stats['in_progress'] += 1
                elif milestone.status == 'PENDING':
                    stats['pending'] += 1
                
                if is_overdue:
                    stats['overdue'] += 1
            
            return Response({
                'status': True,
                'message': 'Project milestones retrieved successfully',
                'count': len(milestones_data),
                'records': milestones_data,
                'stats': stats,
                'project': {
                    'id': str(project.id),
                    'name': project.name,
                    'status': project.status
                },
                'filters': {
                    'search': search,
                    'status': status_filter,
                    'page_size': page_size
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching project milestones',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class ManagerProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # 1. Get the logged-in user
            logged_in_user = request.user

            # 2. Check role
            if logged_in_user.role != "MANAGER":
                return Response({
                    'status': False,
                    'message': 'You are not authorized to view manager projects'
                }, status=status.HTTP_403_FORBIDDEN)

            # 3. Get Employee profile for this manager
            try:
                manager_employee = Employee.objects.select_related("user").get(user=logged_in_user)
            except Employee.DoesNotExist:
                return Response({
                    'status': False,
                    'message': 'Employee profile for this manager not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # 4. Pagination & search
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_project = search_data.get('search', '').strip()

            # Base queryset: only this manager's projects
            projects_queryset = Project.objects.select_related('manager__user').filter(manager=manager_employee)

            # Search filter
            if search_project:
                projects_queryset = projects_queryset.filter(
                    Q(name__icontains=search_project) |
                    Q(description__icontains=search_project) |
                    Q(manager__user__name__icontains=search_project) |
                    Q(manager__user__email__icontains=search_project)
                )

            projects_queryset = projects_queryset.order_by('-created_at')

            # 5. Pagination
            paginator = Paginator(projects_queryset, page_size)
            try:
                paginated_projects = paginator.page(page)
            except Exception:
                paginated_projects = paginator.page(1)

            # 6. Prepare response data
            project_data = []
            for project in paginated_projects:
                project_data.append({
                    'id': str(project.id),
                    'name': project.name,
                    'description': project.description,
                    'status': project.status,
                    'manager': {
                        'id': str(project.manager.id),
                        'user_id': str(project.manager.user.id),
                        'name': project.manager.user.name,
                        'email': project.manager.user.email,
                        'username': project.manager.user.username
                    },
                    'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            return Response({
                'status': True,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'records': project_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
class UploadProjectFiles(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({
                    'status': False,
                    'message': 'project_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)

            files = request.FILES.getlist('files')
            if not files:
                return Response({
                    'status': False,
                    'message': 'No files uploaded'
                }, status=status.HTTP_400_BAD_REQUEST)

            allowed_ext = {'pdf', 'docx', 'xlsx', 'jpg', 'jpeg', 'png'}
            saved = []

            # get uploader employee if exists
            employee = Employee.objects.filter(user=request.user).first()

            # Build base path components
            now = datetime.now()
            year = now.strftime('%Y')      # e.g., '2025'
            month = now.strftime('%m')     # e.g., '08'

            base_dir = 'project_files'     # top-level folder
            year_dir = os.path.join(base_dir, year)
            month_dir = os.path.join(year_dir, month)
            project_dir = os.path.join(month_dir, str(project_id))

            # Ensure directories exist in storage
            # default_storage.path may not exist for storages like S3, so we use exists/save logic.
            for path in [base_dir, year_dir, month_dir, project_dir]:
                if not default_storage.exists(path):
                    # create a placeholder to force directory creation on some backends
                    # then immediately delete it to keep directory clean
                    placeholder = os.path.join(path, '.keep')
                    default_storage.save(placeholder, ContentFile(b''))
                    default_storage.delete(placeholder)

            for f in files:
                if not isinstance(f, UploadedFile):
                    # Skip any non-file item (rare)
                    continue

                original_name = getattr(f, 'name', '')
                # Sanitize filename for safety and portability
                safe_name = get_valid_filename(original_name) or 'file'
                ext = safe_name.split('.')[-1].lower() if '.' in safe_name else ''
                if ext not in allowed_ext:
                    return Response({
                        'status': False,
                        'message': f'Invalid file type: .{ext}'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Final relative path inside storage: project_files/YYYY/MM/<project_id>/<filename>
                relative_path = os.path.join(project_dir, safe_name)

                # If a file with same name exists, default_storage.save will uniquify it by appending suffix
                saved_path = default_storage.save(relative_path, ContentFile(f.read()))

                # Persist record with relative path (Django will resolve it via storage)
                pf = ProjectFile.objects.create(
                    project=project,
                    file=saved_path,      # store the path returned by storage
                    filename=safe_name,
                    extension=ext,
                    size=f.size or 0,
                    uploaded_by=employee
                )

                saved.append({
                    'id': str(pf.id),
                    'filename': pf.filename,
                    'extension': pf.extension,
                    'size': pf.size,
                    'path': saved_path  # relative storage path
                })

            return Response({
                'status': True,
                'message': 'Files uploaded successfully',
                'records': saved
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error uploading files',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProjectFilesList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({
                    'status': False,
                    'message': 'project_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({
                    'status': False,
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Fetch files
            files_qs = ProjectFile.objects.filter(project=project).order_by('-created_at')

            # Build absolute or relative URLs using storage
            records = []
            for pf in files_qs:
                try:
                    url = pf.file.url  # storage-resolved URL
                except Exception:
                    url = None
                records.append({
                    'id': str(pf.id),
                    'filename': pf.filename,
                    'extension': pf.extension,
                    'size': pf.size,
                    'created_at': pf.created_at.strftime('%Y-%m-%d %H:%M:%S') if pf.created_at else None,
                    'url': url,
                })

            return Response({
                'status': True,
                'count': len(records),
                'records': records,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Error fetching project files',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        




