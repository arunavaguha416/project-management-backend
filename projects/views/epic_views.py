from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from projects.models.epic_model import Epic
from projects.models.project_model import Project

from projects.utils.permissions import require_project_manager


class EpicAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            name = request.data.get('name')
            description = request.data.get('description', '')
            color = request.data.get('color', '#36B37E')

            if not project_id or not name:
                return Response({
                    'status': False,
                    'message': 'project_id and name are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_200_OK)

            # 🔐 permission
            require_project_manager(request.user, project)

            epic = Epic.objects.create(
                project=project,
                name=name,
                description=description,
                color=color
            )

            return Response({
                'status': True,
                'message': 'Epic created successfully',
                'records': {'id': str(epic.id), 'name': epic.name}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'An error occurred while adding the epic',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
