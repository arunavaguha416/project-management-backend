from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from projects.models.task_model import Task
from projects.models.sprint_model import Sprint
from projects.models.project_model import Project
from projects.models.epic_model import Epic
from authentication.models.user import User
from projects.serializers.task_serializer import TaskSerializer


class TaskAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            data = request.data or {}

            title = (data.get('title') or '').strip()
            if not title:
                return Response({'status': False, 'message': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)

            project_id = data.get('project_id')
            if not project_id:
                return Response({'status': False, 'message': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

            # Optional FKs
            sprint = None
            sprint_id = data.get('sprint_id')
            if sprint_id:
                sprint = Sprint.objects.filter(id=sprint_id, project=project).first()
                if not sprint:
                    return Response({'status': False, 'message': 'Sprint not found for this project'}, status=status.HTTP_404_NOT_FOUND)

            epic = None
            epic_id = data.get('epic')
            if epic_id:
                epic = Epic.objects.filter(id=epic_id, project=project).first()
                if not epic:
                    return Response({'status': False, 'message': 'Epic not found for this project'}, status=status.HTTP_404_NOT_FOUND)

            assigned_to = None
            assigned_to_id = data.get('assigned_to')
            if assigned_to_id:
                assigned_to = User.objects.filter(id=assigned_to_id).first()
                if not assigned_to:
                    return Response({'status': False, 'message': 'Assigned user not found'}, status=status.HTTP_404_NOT_FOUND)

            # Enums
            status_value = (data.get('status') or 'TODO').upper()
            if status_value not in dict(Task.STATUS_CHOICES):
                return Response({'status': False, 'message': f'Invalid status: {status_value}'}, status=status.HTTP_400_BAD_REQUEST)

            priority_value = (data.get('priority') or 'MEDIUM').upper()
            if priority_value not in dict(Task.PRIORITY_CHOICES):
                return Response({'status': False, 'message': f'Invalid priority: {priority_value}'}, status=status.HTTP_400_BAD_REQUEST)

            task_type_value = (data.get('task_type') or 'TASK').upper()
            if task_type_value not in dict(Task.TYPE_CHOICES):
                return Response({'status': False, 'message': f'Invalid task_type: {task_type_value}'}, status=status.HTTP_400_BAD_REQUEST)

            description = data.get('description') or ''

            # Labels
            labels = data.get('labels')
            if labels is None:
                labels = []
            elif isinstance(labels, str):
                labels = [s.strip() for s in labels.split(',') if s.strip()]
            elif isinstance(labels, list):
                labels = [str(x) for x in labels]
            else:
                return Response({'status': False, 'message': 'labels must be a list or comma-separated string'}, status=status.HTTP_400_BAD_REQUEST)

            # Due date (accept raw string if your model uses DateField with auto parsing elsewhere)
            due_date = data.get('due_date') or None

            story_points = data.get('story_points')
            if story_points is not None:
                try:
                    story_points = int(story_points)
                except Exception:
                    return Response({'status': False, 'message': 'story_points must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

            task = Task.objects.create(
                title=title,
                description=description,
                status=status_value,
                priority=priority_value,
                task_type=task_type_value,
                project=project,
                sprint=sprint,
                assigned_to=assigned_to,
                epic=epic,
                labels=labels,
                due_date=due_date,
                story_points=story_points if story_points is not None else None,
            )

            # Build response
            assignee_name = 'Unassigned'
            if getattr(task, 'assigned_to', None):
                if hasattr(task.assigned_to, 'user') and getattr(task.assigned_to.user, 'name', None):
                    assignee_name = task.assigned_to.user.name
                elif getattr(task.assigned_to, 'username', None):
                    assignee_name = task.assigned_to.username

            record = {
                'id': str(task.id),
                'title': task.title,
                'description': task.description or '',
                'status': task.status,
                'priority': task.priority,
                'task_type': task.task_type,
                'project_id': str(project.id),
                'sprint_id': str(task.sprint.id) if task.sprint else None,
                'assigned_to': str(task.assigned_to.id) if task.assigned_to else None,
                'assignee_name': assignee_name,
                'epic': str(task.epic.id) if task.epic else None,
                'labels': task.labels or [],
                'due_date': task.due_date if task.due_date else None,
                'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else None,
                'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else None,
            }

            return Response({'status': True, 'message': 'Task added successfully', 'records': record}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'An error occurred while adding the task', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
                return Response({'status': False, 'message': 'Please provide sprintId'}, status=status.HTTP_400_BAD_REQUEST)

            query = Q(sprint__id=sprint_id)
            if company_id:
                query &= Q(project__company__id=company_id)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            tasks = Task.objects.filter(query).order_by('-created_at')

            if not tasks.exists():
                return Response({'status': False, 'message': 'Tasks not found'}, status=status.HTTP_200_OK)

            serializer = TaskSerializer(tasks, many=True)
            return Response({'status': True, 'count': tasks.count(), 'records': serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BacklogTaskList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            project_id = search_data.get('project_id', '')
            company_id = search_data.get('company_id', '')
            search_title = search_data.get('title', '')
            search_description = search_data.get('description', '')

            # Keep owner constraint only if your model has it; else remove/replace.
            query = Q()
            if project_id:
                query &= Q(project__id=project_id)
            if company_id:
                query &= Q(project__company__id=company_id)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            query &= Q(sprint__isnull=True)

            tasks = Task.objects.filter(query).order_by('-created_at')

            if not tasks.exists():
                return Response({'status': False, 'message': 'Backlog tasks not found'}, status=status.HTTP_200_OK)

            serializer = TaskSerializer(tasks, many=True)
            return Response({'status': True, 'count': tasks.count(), 'records': serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BacklogSimpleList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            page_size = int(request.data.get('page_size', 50))
            search_title = (request.data.get('title') or '').strip()
            search_description = (request.data.get('description') or '').strip()

            if not project_id:
                return Response({'status': False, 'message': 'Project ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            query = Q(project__id=project_id, sprint__isnull=True)
            if search_title:
                query &= Q(title__icontains=search_title)
            if search_description:
                query &= Q(description__icontains=search_description)

            tasks = Task.objects.filter(query).order_by('-created_at')
            if page_size:
                tasks = tasks[:page_size]

            records = []
            for t in tasks:
                assignee_name = 'Unassigned'
                if getattr(t, 'assigned_to', None):
                    if hasattr(t.assigned_to, 'user') and getattr(t.assigned_to.user, 'name', None):
                        assignee_name = t.assigned_to.user.name
                    elif getattr(t.assigned_to, 'username', None):
                        assignee_name = t.assigned_to.username

                records.append({
                    'id': str(t.id),
                    'title': t.title,
                    'description': t.description or '',
                    'status': t.status,
                    'priority': getattr(t, 'priority', 'MEDIUM'),
                    'assignee_name': assignee_name,
                    'due_date': t.due_date.strftime('%Y-%m-%d') if getattr(t, 'due_date', None) else None,
                    'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(t, 'created_at', None) else None,
                    'updated_at': t.updated_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(t, 'updated_at', None) else None,
                })

            return Response({'status': True, 'count': len(records), 'records': records}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('id')
            if not task_id:
                return Response({'status': False, 'message': 'Please provide taskId'}, status=status.HTTP_400_BAD_REQUEST)

            t = (Task.objects
                 .select_related('project', 'sprint', 'assigned_to', 'epic')
                 .filter(id=task_id)
                 .first())

            if not t:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            record = {
                'id': str(t.id),
                'title': t.title or '',
                'description': t.description or '',
                'status': t.status or 'TODO',
                'priority': t.priority or 'MEDIUM',
                'task_type': getattr(t, 'task_type', 'TASK') or 'TASK',

                'project_id': str(t.project.id) if t.project else None,
                'project_name': t.project.name if t.project and hasattr(t.project, 'name') else None,

                'sprint_id': str(t.sprint.id) if t.sprint else None,
                'sprint_name': t.sprint.name if t.sprint else None,

                'assigned_to': str(t.assigned_to.id) if t.assigned_to else None,
                'assigned_to_name': (
                    getattr(t.assigned_to, 'username', None)
                    or getattr(getattr(t.assigned_to, 'user', None), 'name', None)
                    or None
                ),

                'epic': str(t.epic.id) if getattr(t, 'epic', None) else None,
                'epic_name': t.epic.name if getattr(t, 'epic', None) else None,

                'labels': t.labels or [],
                'due_date': t.due_date.strftime('%Y-%m-%d') if getattr(t, 'due_date', None) else None,

                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(t, 'created_at', None) else None,
                'updated_at': t.updated_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(t, 'updated_at', None) else None,

                'key': getattr(t, 'code', None) or getattr(t, 'key', None),
            }

            return Response({'status': True, 'records': record}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'An error occurred while fetching task details', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            task = Task.objects.filter(id=task_id).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            # Ensure serializer allows task_type, priority, assigned_to, epic, labels, due_date, etc.
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Task updated successfully'}, status=status.HTTP_200_OK)

            return Response({'status': False, 'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': 'An error occurred while updating the task', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            title = request.data.get('title')
            description = request.data.get('description')
            if not task_id:
                return Response({'status': False, 'message': 'id is required'}, status=status.HTTP_400_BAD_REQUEST)

            t = Task.objects.filter(id=task_id).first()
            if not t:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            if title is not None:
                t.title = title
            if description is not None:
                t.description = description
            t.save()

            return Response({'status': True, 'message': 'Details updated'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'Update failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateProperties(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            task_type = request.data.get('task_type')
            priority = request.data.get('priority')

            if not task_id:
                return Response({'status': False, 'message': 'id is required'}, status=status.HTTP_400_BAD_REQUEST)

            t = Task.objects.filter(id=task_id).first()
            if not t:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            if task_type is not None:
                t.task_type = task_type
            if priority is not None:
                t.priority = priority
            t.save()

            return Response({'status': True, 'message': 'Properties updated'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'Update failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateAssignment(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            assigned_to = request.data.get('assigned_to')
            due_date = request.data.get('due_date')

            if not task_id:
                return Response({'status': False, 'message': 'id is required'}, status=status.HTTP_400_BAD_REQUEST)

            t = Task.objects.filter(id=task_id).first()
            if not t:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            if assigned_to in (None, ''):
                t.assigned_to = None
            else:
                user = User.objects.filter(id=assigned_to).first()
                if not user:
                    return Response({'status': False, 'message': 'Assigned user not found'}, status=status.HTTP_200_OK)
                t.assigned_to = user

            if due_date in (None, ''):
                t.due_date = None
            else:
                t.due_date = due_date

            t.save()
            return Response({'status': True, 'message': 'Assignment updated'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'Update failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskUpdateClassification(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            epic = request.data.get('epic')
            labels = request.data.get('labels', [])

            if not task_id:
                return Response({'status': False, 'message': 'id is required'}, status=status.HTTP_400_BAD_REQUEST)

            t = Task.objects.filter(id=task_id).first()
            if not t:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            if epic in (None, ''):
                t.epic = None
            else:
                ep = Epic.objects.filter(id=epic).first()
                if not ep:
                    return Response({'status': False, 'message': 'Epic not found'}, status=status.HTTP_200_OK)
                t.epic = ep

            if labels in (None, ''):
                t.labels = []
            else:
                if isinstance(labels, str):
                    labels = [s.strip() for s in labels.split(',') if s.strip()]
                t.labels = labels

            t.save()
            return Response({'status': True, 'message': 'Classification updated'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': 'Update failed', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskMove(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task_id = request.data.get('id')
            new_status = request.data.get('status')
            sprint_id = request.data.get('sprint_id')

            task = Task.objects.filter(id=task_id).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            if new_status not in dict(Task.STATUS_CHOICES).keys():
                return Response({'status': False, 'message': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

            if sprint_id and not Sprint.objects.filter(id=sprint_id).exists():
                return Response({'status': False, 'message': 'Sprint not found'}, status=status.HTTP_400_BAD_REQUEST)

            task.status = new_status
            if sprint_id is not None:
                # allow move to backlog by sending null
                task.sprint_id = sprint_id
            task.save()

            return Response({'status': True, 'message': 'Task moved successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TaskDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, task_id):
        try:
            task = Task.objects.filter(id=task_id).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            task.soft_delete()
            return Response({'status': True, 'message': 'Task deleted successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RestoreTask(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('id')
            task = Task.all_objects.filter(id=task_id).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            task.deleted_at = None
            task.save()
            return Response({'status': True, 'message': 'Task restored successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
