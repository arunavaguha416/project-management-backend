import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from projects.models.project_model import Project, ProjectFile
from projects.utils.permissions import (
    require_project_viewer,
    require_project_manager
)



class ProjectFileUpload(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            file = request.FILES.get('file')

            if not project_id or not file:
                return Response(
                    {'status': False, 'message': 'project_id and file are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            require_project_manager(request.user, project)

            project_file = ProjectFile.objects.create(
                project=project,
                file=file,              # 🔥 saved into project_files/
                name=file.name,
                size=file.size,
                uploaded_by=request.user
            )

            return Response({
                'status': True,
                'records': {
                    'id': str(project_file.id),
                    'name': project_file.name,
                    'size': project_file.size,
                    'path': project_file.file.name,   # relative path
                    'url': project_file.file.url,     # /project_files/...
                    'uploaded_at': project_file.created_at
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )




class ProjectFileList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response(
                    {'status': False, 'message': 'project_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            require_project_viewer(request.user, project)

            files = ProjectFile.objects.filter(
                project=project
            ).order_by('-created_at')

            records = [{
                'id': str(f.id),
                'name': f.name,
                'size': f.size,
                'path': f.file.name,
                'url': f.file.url,
                'uploaded_by': f.uploaded_by.name if f.uploaded_by else None,
                'uploaded_at': f.created_at
            } for f in files]

            return Response({'status': True, 'records': records})

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )





class ProjectFileDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            file_id = request.data.get('file_id')
            if not file_id:
                return Response(
                    {'status': False, 'message': 'file_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            project_file = ProjectFile.objects.select_related('project').filter(
                id=file_id
            ).first()

            if not project_file:
                return Response(
                    {'status': False, 'message': 'File not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            require_project_manager(request.user, project_file.project)

            # 🔥 Django deletes file from filesystem automatically
            project_file.file.delete(save=False)
            project_file.delete()

            return Response(
                {'status': True, 'message': 'File deleted successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )




