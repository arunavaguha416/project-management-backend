from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db.models import Q
from projects.models.sprint_model import Sprint
from projects.models.project_model import Project
from projects.serializers.sprint_serializer import SprintSerializer
from django.core.paginator import Paginator


class SprintAdd(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            serializer = SprintSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Sprint added successfully',
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
                'message': 'An error occurred while adding the sprint',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SprintList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_name = search_data.get('name', '')
            search_description = search_data.get('description', '')

            query = Q(projects__company__id=search_data.get('company_id', '')) if search_data.get('company_id') else Q()
            if search_name:
                query &= Q(name__icontains=search_name)
            if search_description:
                query &= Q(description__icontains=search_description)

            sprints = Sprint.objects.filter(query).order_by('-created_at')

            if sprints.exists():
                if page is not None:
                    paginator = Paginator(sprints, page_size)
                    paginated_sprints = paginator.get_page(page)
                    serializer = SprintSerializer(paginated_sprints, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = SprintSerializer(sprints, many=True)
                    return Response({
                        'status': True,
                        'count': sprints.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sprints not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SprintDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('id')
            if sprint_id:
                sprint = Sprint.objects.filter(id=sprint_id).values(
                    'id', 'name', 'description', 'start_date', 'end_date', 'projects__id', 'projects__name'
                ).first()
                if sprint:
                    return Response({
                        'status': True,
                        'records': sprint
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Sprint not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide sprintId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching sprint details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SprintUpdate(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            sprint_id = request.data.get('id')
            sprint = Sprint.objects.filter(id=sprint_id).first()
            if sprint:
                serializer = SprintSerializer(sprint, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Sprint updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Sprint not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the sprint',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SprintDelete(APIView):
    permission_classes = (IsAdminUser,)

    def delete(self, request, sprint_id):
        try:
            sprint = Sprint.objects.filter(id=sprint_id).first()
            if sprint:
                sprint.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Sprint deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RestoreSprint(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            sprint_id = request.data.get('id')
            sprint = Sprint.all_objects.get(id=sprint_id)
            if sprint:
                sprint.deleted_at = None
                sprint.save()
                return Response({
                    'status': True,
                    'message': 'Sprint restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AddProjectToSprint(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            project_id = request.data.get('project_id')
            sprint = Sprint.objects.filter(id=sprint_id).first()
            project = Project.objects.filter(id=project_id).first()
            if sprint and project:
                sprint.projects.add(project)
                return Response({
                    'status': True,
                    'message': 'Project added to sprint successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Sprint or project not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RemoveProjectFromSprint(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            project_id = request.data.get('project_id')
            sprint = Sprint.objects.filter(id=sprint_id).first()
            project = Project.objects.filter(id=project_id).first()
            if sprint and project:
                sprint.projects.remove(project)
                return Response({
                    'status': True,
                    'message': 'Project removed from sprint successfully'
                }, status=status.HTTP_200_OK)
            return Response({
                'status': False,
                'message': 'Sprint or project not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)