import os
import uuid
from django.utils.timezone import now
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from projects.models.project_model import Project, ProjectFile
from projects.utils.permissions import (
    require_project_viewer,
    require_project_manager,
    require_project_editor,
    require_project_manager_or_hr
)
from urllib.parse import urlparse
from django.http import FileResponse


class ProjectFileUpload(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get('project_id')
            file = request.FILES.get('file')

            if not project_id or not file:
                return Response({'status': False, 'message': 'Invalid upload'}, status=400)

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=404)

            require_project_editor(request.user, project)

            today = now()
            folder = os.path.join(
                settings.MEDIA_ROOT,
                'project_files',
                str(project.id),
                today.strftime('%Y'),
                today.strftime('%m'),
                today.strftime('%d')
            )
            os.makedirs(folder, exist_ok=True)

            system_filename = f"{uuid.uuid4()}{os.path.splitext(file.name)[1]}"
            file_path = os.path.join(folder, system_filename)

            with open(file_path, 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)

            project_file = ProjectFile.objects.create(
                project=project,
                uploaded_by=request.user,
                file_path=file_path,
                original_name=file.name
            )

            project_file.file_url = request.build_absolute_uri(
                f"/api/projects/files/download/{project_file.id}/"
            )
            project_file.save()

            return Response({'status': True}, status=200)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=400)






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
            file = ProjectFile.objects.select_related('project').filter(id=file_id).first()

            if not file:
                return Response({'status': False, 'message': 'File not found'}, status=404)

            require_project_manager(request.user, file.project)

            # 🔥 DELETE FILE SAFELY
            if os.path.exists(file.file_path):
                os.remove(file.file_path)

            file.delete()

            return Response({'status': True}, status=200)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=400)



class ProjectFileDownload(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, file_id):
        try:
            file = ProjectFile.objects.select_related('project').filter(id=file_id).first()
            if not file:
                return Response(
                    {'status': False, 'message': 'File not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            project = file.project

            # 🔒 Permission check
            require_project_editor(request.user, project)

            # 🔒 File existence
            if not file.file_path or not os.path.exists(file.file_path):
                return Response(
                    {'status': False, 'message': 'File missing on server'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # ✅ Stream file
            response = FileResponse(
                open(file.file_path, 'rb'),
                as_attachment=True,
                filename=file.original_name
            )

            return response

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


