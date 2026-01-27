from datetime import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from projects.models.task_model import Task
from projects.models.sprint_model import Sprint
from projects.utils.permissions import require_project_editor,require_project_manager
from projects.utils.sprint_ai_plan_compare import compare_plans
from projects.utils.sprint_capacity_service import calculate_sprint_capacity
from projects.utils.sprint_plan_ai_service import generate_sprint_plan


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
            
            if task.sprint_id:
                return Response({
                    "status": False,
                    "message": "Task already in sprint"
                }, status=200)


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
# ------------------------------------------------------------------
#AI Sprint Planning
# ------------------------------------------------------------------

class SprintPlanSuggestionView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        sprint_id = request.data.get("sprint_id")

        sprint = Sprint.objects.get(id=sprint_id)

        # -----------------------------
        # 1️⃣ Current manual plan snapshot
        # -----------------------------
        sprint_tasks = Task.objects.filter(
            sprint=sprint,
            deleted_at__isnull=True
        )

        manual_capacity = calculate_sprint_capacity(sprint)

        manual_plan = {
            "capacity_used": sum(
                t.story_points or 0 for t in sprint_tasks
            ),
            "overloaded_users": [
                a["employee_id"]
                for a in manual_capacity["assignees"]
                if (
                    sum(
                        t.story_points or 0
                        for t in sprint_tasks
                        if t.assigned_to_id == a["employee_id"]
                    ) > a["capacity_points"]
                )
            ]
        }

        # -----------------------------
        # 2️⃣ AI plan generation
        # -----------------------------
        backlog_tasks = Task.objects.filter(
            sprint__isnull=True,
            project=sprint.project,
            deleted_at__isnull=True
        )

        ai_plan = generate_sprint_plan(sprint, backlog_tasks)

        # -----------------------------
        # 3️⃣ Compare plans (HERE!)
        # -----------------------------
        comparison = compare_plans(
            manual=manual_plan,
            ai=ai_plan
        )

        # -----------------------------
        # 4️⃣ Single response
        # -----------------------------
        return Response({
            "status": True,
            "records": {
                "ai_plan": ai_plan,
                "comparison": comparison
            }
        })


class SprintPlanningView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, sprint_id):
        try:
            sprint = Sprint.objects.filter(id=sprint_id).first()
            if not sprint:
                return Response({
                    'status': False,
                    'message': 'Sprint not found'
                }, status=status.HTTP_404_NOT_FOUND)

            tasks = Task.objects.filter(sprint=sprint).order_by('priority')

            records = []
            for t in tasks:
                records.append({
                    'id': str(t.id),
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'assigned_to': t.assigned_to.user.name if t.assigned_to else None,
                    'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None,
                    'is_overdue': bool(
                        t.due_date and
                        t.due_date < timezone.now().date() and
                        t.status != 'DONE'
                    )
                })

            return Response({
                'status': True,
                'records': {
                    'sprint': {
                        'id': str(sprint.id),
                        'name': sprint.name,
                        'status': sprint.status
                    },
                    'tasks': records
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Failed to load sprint planning',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
