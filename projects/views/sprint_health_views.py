from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from projects.models.sprint_model import Sprint
from projects.utils.permissions import require_project_viewer
from projects.utils.sprint_health_service import calculate_sprint_health

class SprintHealthReport(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get('sprint_id')
            if not sprint_id:
                return Response(
                    {'status': False, 'message': 'sprint_id is required'},
                    status=400
                )

            sprint = Sprint.objects.select_related('project').filter(id=sprint_id).first()
            if not sprint:
                return Response(
                    {'status': False, 'message': 'Sprint not found'},
                    status=200
                )

            require_project_viewer(request.user, sprint.project)

            report = calculate_sprint_health(sprint)

            return Response({
                'status': True,
                'records': report
            }, status=200)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=400
            )
