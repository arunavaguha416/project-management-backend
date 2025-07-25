from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from projects.models.task_model import Task
from projects.serializers.task_serializer import TaskSerializer
from django.core.paginator import Paginator
from projects.models.sprint_model import Sprint


class TaskAdd(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': True,
                    'message': 'Task added successfully',
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
                'message': 'An error occurred while adding the task',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class SprintTaskList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            sprint_id = search_data.get('sprint_id')
            search_title = search_data.get('title', '')
            search_description = search_data.get('description', '')
            company_id = search_data.get('company_id', '')

            if not sprint_id:
                return Response({
                    'status': False,
                    'message': 'Please provide sprintId'
                }, status=status.HTTP_400_BAD_REQUEST)

            query = Q(sprint__id=sprint_id, project__company__id=company_id) if company_id else Q(sprint__id=sprint_id)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            tasks = Task.objects.filter(query).order_by('-created_at')

            if tasks.exists():
                serializer = TaskSerializer(tasks, many=True)
                return Response({
                    'status': True,
                    'count': tasks.count(),
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Tasks not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class BacklogTaskList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            project_id = search_data.get('project_id', '')
            company_id = search_data.get('company_id', '')
            search_title = search_data.get('title', '')
            search_description = search_data.get('description', '')

            query = Q(project__owner=request.user)
            if project_id:
                query &= Q(project__id=project_id)
            if company_id:
                query &= Q(project__company__id=company_id)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)
            query &= Q(sprint__isnull=True)  # Tasks not assigned to any sprint (backlog)

            tasks = Task.objects.filter(query).order_by('-created_at')

            if tasks.exists():
                serializer = TaskSerializer(tasks, many=True)
                return Response({
                    'status': True,
                    'count': tasks.count(),
                    'records': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Backlog tasks not found',
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TaskDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('id')
            if task_id:
                task = Task.objects.filter(
                    id=task_id, project__owner=request.user
                ).values('id', 'title', 'description', 'status', 'priority', 'project__name', 'sprint__name', 'assigned_to__username').first()
                if task:
                    return Response({
                        'status': True,
                        'records': task
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Task not found',
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Please provide taskId'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while fetching task details',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TaskUpdate(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            task = Task.objects.filter(id=task_id).first()
            if task:
                serializer = TaskSerializer(task, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': True,
                        'message': 'Task updated successfully'
                    }, status=status.HTTP_200_OK)
                return Response({
                    'status': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': False,
                'message': 'Task not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while updating the task',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TaskMove(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            new_status = request.data.get('status')
            sprint_id = request.data.get('sprint_id')
            task = Task.objects.filter(id=task_id).first()
            if not task:
                return Response({
                    'status': False,
                    'message': 'Task not found'
                }, status=status.HTTP_200_OK)
            if new_status not in dict(Task.STATUS_CHOICES).keys():
                return Response({
                    'status': False,
                    'message': 'Invalid status'
                }, status=status.HTTP_400_BAD_REQUEST)
            if sprint_id and not Sprint.objects.filter(id=sprint_id).exists():
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            task.status = new_status
            if sprint_id:
                task.sprint_id = sprint_id
            task.save()
            return Response({
                'status': True,
                'message': 'Task moved successfully'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class TaskDelete(APIView):
    permission_classes = (IsAdminUser,)

    def delete(self, request, task_id):
        try:
            task = Task.objects.filter(id=task_id).first()
            if task:
                task.soft_delete()
                return Response({
                    'status': True,
                    'message': 'Task deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                'status': False,
                'message': 'Task not found'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RestoreTask(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            task_id = request.data.get('id')
            task = Task.all_objects.get(id=task_id)
            if task:
                task.deleted_at = None
                task.save()
                return Response({
                    'status': True,
                    'message': 'Task restored successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Task not found'
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)