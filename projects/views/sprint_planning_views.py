from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from projects.models.task_model import Task
from projects.models.sprint_model import Sprint
from projects.utils.permissions import require_project_editor


# ------------------------------------------------------------------
# Add Task to Sprint (SPRINT PLANNING)
# ------------------------------------------------------------------
class AddTaskToSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get("task_id")
            sprint_id = request.data.get("sprint_id")

            if not task_id or not sprint_id:
                return Response(
                    {"status": False, "message": "task_id and sprint_id are required"},
                    status=status.HTTP_200_OK
                )

            task = Task.objects.select_related("project").filter(
                id=task_id,
                deleted_at__isnull=True
            ).first()

            if not task:
                return Response(
                    {"status": False, "message": "Task not found"},
                    status=status.HTTP_200_OK
                )

            sprint = Sprint.objects.filter(id=sprint_id).first()
            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            if sprint.project_id != task.project_id:
                return Response(
                    {"status": False, "message": "Task and sprint belong to different projects"},
                    status=status.HTTP_200_OK
                )

            if sprint.status == "COMPLETED":
                return Response(
                    {"status": False, "message": "Cannot modify a completed sprint"},
                    status=status.HTTP_200_OK
                )

            # 🔐 RBAC
            require_project_editor(request.user, sprint.project)

            task.sprint = sprint
            task.save(update_fields=["sprint"])

            return Response(
                {"status": True, "message": "Task added to sprint successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Remove Task from Sprint (BACKLOG)
# ------------------------------------------------------------------
class RemoveTaskFromSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get("task_id")

            if not task_id:
                return Response(
                    {"status": False, "message": "task_id is required"},
                    status=status.HTTP_200_OK
                )

            task = Task.objects.select_related("project", "sprint").filter(
                id=task_id,
                deleted_at__isnull=True
            ).first()

            if not task:
                return Response(
                    {"status": False, "message": "Task not found"},
                    status=status.HTTP_200_OK
                )

            if not task.sprint:
                return Response(
                    {"status": False, "message": "Task is already in backlog"},
                    status=status.HTTP_200_OK
                )

            if task.sprint.status == "COMPLETED":
                return Response(
                    {"status": False, "message": "Cannot modify a completed sprint"},
                    status=status.HTTP_200_OK
                )

            # 🔐 RBAC
            require_project_editor(request.user, task.project)

            task.sprint = None
            task.save(update_fields=["sprint"])

            return Response(
                {"status": True, "message": "Task moved to backlog"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Bulk Add Tasks to Sprint
# ------------------------------------------------------------------
class BulkAddTasksToSprint(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")
            task_ids = request.data.get("task_ids", [])

            if not sprint_id or not isinstance(task_ids, list):
                return Response(
                    {"status": False, "message": "sprint_id and task_ids[] are required"},
                    status=status.HTTP_200_OK
                )

            sprint = Sprint.objects.filter(id=sprint_id).first()
            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            if sprint.status == "COMPLETED":
                return Response(
                    {"status": False, "message": "Cannot modify a completed sprint"},
                    status=status.HTTP_200_OK
                )

            # 🔐 RBAC
            require_project_editor(request.user, sprint.project)

            tasks = Task.objects.filter(
                id__in=task_ids,
                project=sprint.project,
                deleted_at__isnull=True
            )

            updated = tasks.update(sprint=sprint)

            return Response(
                {
                    "status": True,
                    "message": "Tasks added to sprint",
                    "records": {"updated": updated}
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


