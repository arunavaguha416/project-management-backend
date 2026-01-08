from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone

from projects.models.sprint_model import Sprint
from projects.models.project_model import Project
from projects.models.task_model import Task
from projects.models.comments_model import Comment
from projects.serializers.sprint_serializer import SprintSerializer
from projects.models.task_model import TaskStatusHistory
from projects.utils.sprint_ai_utils import calculate_sprint_ai_completion
from projects.utils.permissions import (
    require_project_viewer,
    require_project_manager,
    require_project_owner,
)

# ------------------------------------------------------------------
# Sprint List (READ)
# ------------------------------------------------------------------
class SprintList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            page = request.data.get('page')
            page_size = request.data.get('page_size', 10)

            if not project_id:
                return Response({'status': False, 'message': 'project_id is required'},
                                status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'},
                                status=status.HTTP_200_OK)

            require_project_viewer(request.user, project)

            sprints = Sprint.objects.filter(project=project).order_by('-created_at')

            if not sprints.exists():
                return Response({'status': False, 'message': 'Sprints not found'},
                                status=status.HTTP_200_OK)

            if page:
                paginator = Paginator(sprints, page_size)
                page_obj = paginator.get_page(page)
                serializer = SprintSerializer(page_obj, many=True)
                return Response({
                    'status': True,
                    'count': paginator.count,
                    'num_pages': paginator.num_pages,
                    'records': serializer.data
                })

            serializer = SprintSerializer(sprints, many=True)
            return Response({'status': True, 'count': sprints.count(), 'records': serializer.data})

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=400)


# ------------------------------------------------------------------
# Sprint Update (PLANNED only)
# ------------------------------------------------------------------
class SprintUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            sprint = Sprint.objects.select_related('project').filter(
                id=request.data.get('id')
            ).first()

            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'})

            require_project_manager(request.user, sprint.project)

            if sprint.status != 'PLANNED':
                return Response({
                    'status': False,
                    'message': 'Only PLANNED sprints can be updated'
                }, status=status.HTTP_200_OK)

            serializer = SprintSerializer(sprint, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True, 'message': 'Sprint updated successfully'})

            return Response({'status': False, 'errors': serializer.errors})

        except Exception as e:
            return Response({'status': False, 'message': str(e)})



# ------------------------------------------------------------------
# Sprint Delete (PLANNED only)
# ------------------------------------------------------------------
class SprintDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, sprint_id):
        try:
            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'})

            require_project_owner(request.user, sprint.project)

            if sprint.status != 'PLANNED':
                return Response({
                    'status': False,
                    'message': 'Only PLANNED sprint can be deleted'
                })

            sprint.soft_delete()
            return Response({'status': True, 'message': 'Sprint deleted successfully'})

        except Exception as e:
            return Response({'status': False, 'message': str(e)})


# ------------------------------------------------------------------
# Sprint Summary (READ)
# ------------------------------------------------------------------
class SprintSummary(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint = Sprint.objects.select_related('project').filter(
                id=request.data.get('id')
            ).first()

            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'},
                                status=status.HTTP_200_OK)

            require_project_viewer(request.user, sprint.project)
            ai_probability = calculate_sprint_ai_completion(sprint)
            task_counts = Task.objects.filter(sprint=sprint).aggregate(
                total_tasks=Count('id'),
                todo_tasks=Count('id', filter=Q(status='TODO')),
                in_progress_tasks=Count('id', filter=Q(status='IN_PROGRESS')),
                done_tasks=Count('id', filter=Q(status='DONE')),
            )

            comment_count = Comment.objects.filter(task__sprint=sprint).count()

            return Response({
                'status': True,
                'records': {
                    'sprint': SprintSerializer(sprint).data,
                    'task_summary': task_counts,
                    'comment_count': comment_count,
                    "ai_completion_probability": ai_probability,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        


# ------------------------------------------------------------------
# Sprint Details (READ)
# ------------------------------------------------------------------
class SprintDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint = Sprint.objects.select_related('project').filter(
                id=request.data.get('id')
            ).first()

            if not sprint:
                return Response({'status': False, 'message': 'Sprint not found'},
                                status=status.HTTP_200_OK)

            require_project_viewer(request.user, sprint.project)

            record = {
                'id': sprint.id,
                'name': sprint.name,
                'description': sprint.description,
                'start_date': sprint.start_date,
                'end_date': sprint.end_date,
                'project__id': sprint.project.id,
                'project__name': sprint.project.name
            }

            return Response({'status': True, 'records': record},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        

# ------------------------------------------------------------------
# Sprint End (MANAGER) — WITH SPILLOVER LOGIC
# ------------------------------------------------------------------
class SprintEnd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint = Sprint.objects.select_related("project").filter(
                id=request.data.get("sprint_id")
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            # 🔐 RBAC
            require_project_manager(request.user, sprint.project)

            if sprint.status != "ACTIVE":
                return Response(
                    {
                        "status": False,
                        "message": "Only ACTIVE sprint can be completed"
                    },
                    status=status.HTTP_200_OK
                )

            # --------------------------------------------------
            # 1. Spillover unfinished tasks to backlog
            # --------------------------------------------------
            spillover_tasks = Task.objects.filter(
                sprint=sprint,
                status__in=["TODO", "IN_PROGRESS"],
                deleted_at__isnull=True
            )

            for task in spillover_tasks:
                old_sprint_id = task.sprint_id

                task.sprint = None
                task.save(update_fields=["sprint"])

                # 🧾 Audit history
                TaskStatusHistory.objects.create(
                    task=task,
                    action="SPRINT_SPILLOVER",
                    from_status=task.status,
                    to_status=task.status,
                    metadata={
                        "from_sprint": str(old_sprint_id),
                        "to_sprint": None
                    },
                    created_by=request.user
                )

            # --------------------------------------------------
            # 2. Complete sprint
            # --------------------------------------------------
            sprint.status = "COMPLETED"
            sprint.end_date = timezone.now().date()
            sprint.save(update_fields=["status", "end_date"])

            return Response(
                {
                    "status": True,
                    "message": "Sprint completed successfully",
                    "records": {
                        "spillover_tasks": spillover_tasks.count()
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )