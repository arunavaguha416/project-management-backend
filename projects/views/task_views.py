from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.db.models import Q
from projects.models.task_model import Task
from projects.serializers.task_serializer import TaskSerializer
from django.core.paginator import Paginator
import datetime

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

class TaskList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_title = search_data.get('title', '')
            search_description = search_data.get('description', '')

            query = Q(project__owner=request.user)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            tasks = Task.objects.filter(query).order_by('-created_at')

            if tasks.exists():
                if page is not None:
                    paginator = Paginator(tasks, page_size)
                    paginated_tasks = paginator.get_page(page)
                    serializer = TaskSerializer(paginated_tasks, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
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

class PublishedTaskList(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            tasks = Task.objects.filter(published_at__isnull=False).values('id', 'title').order_by('-created_at')
            if tasks.exists():
                return Response({
                    'status': True,
                    'records': tasks
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

class DeletedTaskList(APIView):
    permission_classes = (IsAdminUser,)

    def post(self, request):
        try:
            search_data = request.data
            page = search_data.get('page')
            page_size = search_data.get('page_size', 10)
            search_title = search_data.get('title', '')
            search_description = search_data.get('description', '')

            query = Q(deleted_at__isnull=False)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            tasks = Task.all_objects.filter(query).order_by('-created_at')

            if tasks.exists():
                if page is not None:
                    paginator = Paginator(tasks, page_size)
                    paginated_tasks = paginator.get_page(page)
                    serializer = TaskSerializer(paginated_tasks, many=True)
                    return Response({
                        'status': True,
                        'count': paginator.count,
                        'num_pages': paginator.num_pages,
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = TaskSerializer(tasks, many=True)
                    return Response({
                        'status': True,
                        'count': tasks.count(),
                        'records': serializer.data
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': False,
                    'message': 'Deleted tasks not found',
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
                task = Task.objects.filter(id=task_id, project__owner=request.user).values(
                    'id', 'title', 'description', 'status', 'priority'
                ).first()
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

class ChangeTaskPublishStatus(APIView):
    permission_classes = (IsAdminUser,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            publish = request.data.get('status')
            if publish == 1:
                data = {'published_at': datetime.datetime.now()}
            elif publish == 0:
                data = {'published_at': None}
            task = Task.objects.get(id=task_id)
            serializer = TaskSerializer(task, data=data, partial=True)
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