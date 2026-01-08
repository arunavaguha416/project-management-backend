from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from projects.models.task_model import Task
from projects.models.task_model import TaskStatusHistory
from projects.utils.permissions import require_project_viewer


# ---------------------------------------------------------
# Task Status Timeline (READ ONLY)
# ---------------------------------------------------------
class TaskStatusTimeline(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            task_id = request.data.get('task_id')

            if not task_id:
                return Response(
                    {'status': False, 'message': 'task_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            task = Task.objects.select_related('project').filter(
                id=task_id
            ).first()

            if not task:
                return Response(
                    {'status': False, 'message': 'Task not found'},
                    status=status.HTTP_200_OK
                )

            # --------------------------------------------------
            # 🔐 Project RBAC
            # --------------------------------------------------
            require_project_viewer(request.user, task.project)

            # --------------------------------------------------
            # Fetch status history
            # --------------------------------------------------
            history_qs = TaskStatusHistory.objects.filter(
                task=task
            ).order_by('-changed_at')

            records = []
            for h in history_qs:
                records.append({
                    'id': str(h.id),
                    'from_status': h.from_status,
                    'to_status': h.to_status,
                    'changed_by': {
                        'id': str(h.changed_by.id) if h.changed_by else None,
                        'name': h.changed_by.name if h.changed_by else None,
                        'email': h.changed_by.email if h.changed_by else None,
                    },
                    'changed_at': h.changed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'project_id': str(h.project_id),
                    'sprint_id': str(h.sprint_id) if h.sprint_id else None
                })

            return Response({
                'status': True,
                'count': len(records),
                'records': records
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
