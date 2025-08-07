from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from projects.models.project_model import Project, Company
from projects.serializers.project_serializer import ProjectSerializer
from django.core.paginator import Paginator
import datetime
from projects.models.task_model import Task

class ProjectAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            data = request.data.copy()
            data['owner'] = request.user.id
            
            project = Project.objects.create(                    
                    name=data.get('name'),
                    description=data.get('description'),
                    company_id=data.get('company_id'),
                    manager_id=data.get('manager_id'),
                    team_id=data.get('team_id'),
                    # phone=data.get('phone', '')  # Uncomment if you want phone support
                )
            # Use serializer for Employee representation in response
            project_data = ProjectSerializer(project).data
            if project_data:                
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

            # Build query: only projects that match search string (or all if empty)
            query = Q()
            if search_project:
                query &= (
                    Q(name__icontains=search_project) |
                    Q(description__icontains=search_project) |                    
                    Q(manager__name__icontains=search_project)
                )

            # Optional example: filter to only user's projects
            # query &= Q(owner=request.user)  # Uncomment if you want to restrict!

            projects = Project.objects.filter(query).order_by('-created_at')

            if projects.exists():
                paginator = Paginator(projects, page_size)
                try:
                    paginated_projects = paginator.page(page)
                except Exception:
                    paginated_projects = paginator.page(1)
                serializer = ProjectSerializer(paginated_projects, many=True)
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'records': serializer.data
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
            project = Project.objects.select_related('manager', 'client').filter(id=id).first()
            if not project:
                return Response({'status': False, 'message': 'Not found'}, status=404)
            data = {
                'id': str(project.id),
                'name': project.name,
                'manager_name': project.manager.name if project.manager else None,
                'start_date': project.start_date,
                'end_date': project.end_date,
                'status': project.status,
                'client_name': project.client.name if project.client else None,
                'current_sprint': getattr(project, 'current_sprint', None),
            }
            tasks = Task.objects.filter(project=project)
            task_data = [{'id': t.id, 'title': t.title, 'assigned_to_name': t.assigned_to.name if t.assigned_to else None, 'status': t.status} for t in tasks]

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
    
