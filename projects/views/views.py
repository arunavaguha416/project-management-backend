from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from projects.models.project_model import Project
from projects.serializers.project_serializer import ProjectSerializer
from django.core.paginator import Paginator
import datetime

class ProjectAdd(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            serializer = ProjectSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=request.user)
                return Response({
                    'status': True,
                    'message': 'Project added successfully',
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
                'message': 'An error occurred while adding the project',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')

            query = Q(owner=request.user)
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)

            projects = Project.objects.filter(query).order_by('-created_at')

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
                    'message': 'Projects not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PublishedProjectList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            projects = Project.objects.filter(published_at__isnull=False).values('id', 'name').order_by('-created_at')
            if projects.exists():
                return Response({
                    'status': True,
                    'records': projects
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Projects not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeletedProjectList(APIView):
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
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('id')
            if project_id:
                project = Project.objects.filter(id=project_id, owner=request.user).values('id', 'name', 'description').first()
                if project:
                    return Response({
                        'status': True,
                        'records': project
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Project not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide projectId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching project details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ProjectUpdate(APIView):
    permission_classes = (IsAdminUser,)

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

class ChangeProjectPublishStatus(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            project_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            project = Project.objects.get(id=project_id)
            serializer = ProjectSerializer(project, data=data, partial=True)
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

class ProjectDelete(APIView):
    permission_classes = (IsAdminUser,)

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
    permission_classes = (IsAdminUser,)

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