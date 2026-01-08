from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.paginator import Paginator

from projects.models.task_model import Task
from projects.models.project_model import Project
from projects.models.sprint_model import Sprint
from projects.serializers.task_serializer import TaskSerializer
from projects.utils.workflow_validator import validate_task_transition
from projects.utils.permissions import (
    require_project_viewer,
    require_project_editor,
    require_project_manager,
    require_project_owner,
)
from projects.utils.workflow_validator import validate_task_transition
from projects.models.task_model import TaskStatusHistory

# ------------------------------------------------------------------
# Sprint Task List (READ)
# ------------------------------------------------------------------
class SprintTaskList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')

            sprint = Sprint.objects.select_related('project').filter(
                id=sprint_id,
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {'status': False, 'message': 'Sprint not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 Project membership guard
            require_project_viewer(request.user, sprint.project)

            # ✅ SAFE ordering (no missing field)
            tasks = Task.objects.filter(
                sprint=sprint,
                deleted_at__isnull=True
            ).order_by('created_at', 'id')

            serializer = TaskSerializer(tasks, many=True)

            return Response(
                {'status': True, 'records': serializer.data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Backlog Task List (READ)
# ------------------------------------------------------------------
class BacklogTaskList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get("project_id")
            if not project_id:
                return Response(
                    {"status": False, "message": "project_id is required"},
                    status=status.HTTP_200_OK
                )

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=status.HTTP_200_OK
                )

            # 🔐 Viewer access is enough
            require_project_viewer(request.user, project)

            # --------------------------------------------------
            # Backlog = tasks with NO sprint
            # --------------------------------------------------
            tasks = Task.objects.filter(
                project=project,
                sprint__isnull=True,
                deleted_at__isnull=True
            ).order_by("created_at")  # backlog ordering

            records = [{
                "id": str(t.id),
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "task_type": t.task_type,
                "assigned_to": t.assigned_to.name if t.assigned_to else None,
                "story_points": t.story_points,
            } for t in tasks]

            return Response(
                {"status": True, "records": records},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



# ------------------------------------------------------------------
# Simple Backlog List (READ)
# ------------------------------------------------------------------
class BacklogSimpleList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_200_OK)

            require_project_viewer(request.user, project)

            tasks = Task.objects.filter(
                project=project,
                sprint__isnull=True,
                deleted_at__isnull=True
            ).values('id', 'title')

            return Response({'status': True, 'records': list(tasks)}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Details (READ)
# ------------------------------------------------------------------
class TaskDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('id')
            task = Task.objects.select_related('project').filter(id=task_id).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_viewer(request.user, task.project)

            serializer = TaskSerializer(task)
            return Response({'status': True, 'records': serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Create (WRITE)
# ------------------------------------------------------------------
class TaskAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            
            # --------------------------------------------------
            # Project (MANDATORY)
            # --------------------------------------------------
            project_id = request.data.get("project_id")
            if not project_id:
                return Response(
                    {"status": False, "message": "project_id is required"},
                    status=status.HTTP_200_OK
                )

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=status.HTTP_200_OK
                )

            # 🔐 RBAC
            require_project_editor(request.user, project)

            # --------------------------------------------------
            # Optional Sprint
            # --------------------------------------------------
            sprint = None
            sprint_id = request.data.get("sprint_id")
            if sprint_id:
                sprint = Sprint.objects.filter(
                    id=sprint_id,
                    project=project
                ).first()

            # --------------------------------------------------
            # ✅ CREATE TASK (ONLY MODEL FIELDS)
            # --------------------------------------------------
            task = Task(
                title=request.data.get("title"),
                description=request.data.get("description"),
                task_type=request.data.get("task_type", "TASK"),
                priority=request.data.get("priority", "MEDIUM"),
                status=request.data.get("status", "TODO"),
                story_points=request.data.get("story_points", 0),
                due_date=request.data.get("due_date"),
                sprint_id = request.data.get("sprint_id"), 
            )

            # 🔥 REQUIRED FK
            task.project = project

            # Optional relations
            if sprint:
                task.sprint = sprint

            if request.data.get("assigned_to"):
                task.assigned_to_id = request.data.get("assigned_to")

            task.save()

            return Response(
                {
                    "status": True,
                    "message": "Task created successfully",
                    "records": {
                        "id": str(task.id),
                        "title": task.title,
                        "status": task.status,
                        "project_id": str(project.id),
                        "sprint_id": str(task.sprint.id) if task.sprint else None,
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# ------------------------------------------------------------------
# Task Update – Details (WRITE)
# ------------------------------------------------------------------
class TaskUpdateDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task = Task.objects.select_related('project').filter(id=request.data.get('id')).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_editor(request.user, task.project)

            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Task updated successfully'},
                                status=status.HTTP_200_OK)

            return Response({'status': False, 'message': 'Invalid data', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Update – Properties (WRITE)
# ------------------------------------------------------------------
class TaskUpdateProperties(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task = Task.objects.select_related('project').filter(id=request.data.get('id')).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_editor(request.user, task.project)

            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Task properties updated successfully'},
                                status=status.HTTP_200_OK)

            return Response({'status': False, 'message': 'Invalid data', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Update – Assignment (MANAGER)
# ------------------------------------------------------------------
class TaskUpdateAssignment(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task = Task.objects.select_related('project').filter(id=request.data.get('id')).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_manager(request.user, task.project)

            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Task assignment updated successfully'},
                                status=status.HTTP_200_OK)

            return Response({'status': False, 'message': 'Invalid data', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Update – Classification (WRITE)
# ------------------------------------------------------------------
class TaskUpdateClassification(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            task = Task.objects.select_related('project').filter(id=request.data.get('id')).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_editor(request.user, task.project)

            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Task classification updated successfully'},
                                status=status.HTTP_200_OK)

            return Response({'status': False, 'message': 'Invalid data', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Move (WRITE)
# ------------------------------------------------------------------
class TaskMove(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # --------------------------------------------------
            # Fetch task (project resolved here)
            # --------------------------------------------------
            task = Task.objects.select_related('project', 'sprint').filter(
                id=request.data.get('id')
            ).first()

            if not task:
                return Response(
                    {'status': False, 'message': 'Task not found'},
                    status=status.HTTP_200_OK
                )

            # --------------------------------------------------
            # Project RBAC (existing rule)
            # --------------------------------------------------
            require_project_editor(request.user, task.project)

            sprint_id = request.data.get('sprint_id')
            new_status = request.data.get('status')
            new_order = request.data.get('order', task.order)

            old_status = task.status
            old_sprint = task.sprint

            # --------------------------------------------------
            # 🔥 WORKFLOW VALIDATION (status change only)
            # --------------------------------------------------
            if new_status and new_status != old_status:
                validate_task_transition(
                    task=task,
                    new_status=new_status,
                    user=request.user
                )

            # --------------------------------------------------
            # Sprint change (cross-project safe)
            # --------------------------------------------------
            if sprint_id:
                sprint = Sprint.objects.filter(
                    id=sprint_id,
                    project=task.project
                ).first()

                if not sprint:
                    return Response(
                        {'status': False, 'message': 'Invalid sprint'},
                        status=status.HTTP_200_OK
                    )

                task.sprint = sprint
            else:
                task.sprint = None

            # --------------------------------------------------
            # Update task fields
            # --------------------------------------------------
            task.status = new_status or task.status
            task.order = new_order
            task.save()

            # --------------------------------------------------
            # 🔥 AUDIT LOG (TaskStatusHistory)
            # --------------------------------------------------
            if new_status and old_status != new_status:
                TaskStatusHistory.objects.create(
                    task=task,
                    from_status=old_status,
                    to_status=new_status,
                    changed_by=request.user,
                    sprint_id=str(task.sprint.id) if task.sprint else None,
                    project_id=str(task.project.id)
                )

            return Response(
                {'status': True, 'message': 'Task moved successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Task Delete (OWNER)
# ------------------------------------------------------------------
class TaskDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, task_id):
        try:
            task = Task.objects.select_related('project').filter(id=task_id).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_owner(request.user, task.project)

            task.soft_delete()
            return Response({'status': True, 'message': 'Task deleted successfully'},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------
# Task Restore (OWNER)
# ------------------------------------------------------------------
class RestoreTask(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task = Task.all_objects.select_related('project').filter(id=request.data.get('id')).first()
            if not task:
                return Response({'status': False, 'message': 'Task not found'}, status=status.HTTP_200_OK)

            require_project_owner(request.user, task.project)

            task.deleted_at = None
            task.save()

            return Response({'status': True, 'message': 'Task restored successfully'},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
