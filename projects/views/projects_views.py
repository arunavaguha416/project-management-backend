from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from django.http import HttpResponse
from django.utils import timezone
from projects.models.sprint_model import Sprint
from django.conf import settings
from io import BytesIO
from datetime import datetime, date
import os
import uuid

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from projects.models.epic_model import *
from projects.models.project_model import *
from projects.models.task_model import Task
from projects.models.project_member_model import ProjectMember
from projects.serializers.project_serializer import ProjectSerializer

from hr_management.models.hr_management_models import Employee
from authentication.models.user import User
from projects.models.workflow_model import *
from rest_framework.parsers import MultiPartParser, FormParser

from projects.utils.permissions import (
    require_project_viewer,
    require_project_manager,
    require_project_owner,
    require_project_manager_or_hr
)

# ------------------------------------------------------------------
# Project Add
# ------------------------------------------------------------------
class ProjectAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            data = request.data.copy()

            # -------------------------------------------------
            # Resolve company from logged-in user
            # -------------------------------------------------
            creator_employee = Employee.objects.filter(user=request.user).first()
            if not creator_employee:
                return Response(
                    {'status': False, 'message': 'Employee record not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            company = creator_employee.company

            # -------------------------------------------------
            # Resolve manager (Employee)
            # -------------------------------------------------
            manager = None
            manager_id = data.get('manager_id')
            if manager_id:
                manager = Employee.objects.filter(
                    user_id=manager_id,
                    company=company
                ).first()

                if not manager:
                    return Response(
                        {'status': False, 'message': 'Invalid manager'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # -------------------------------------------------
            # Create project
            # -------------------------------------------------
            project = Project.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                manager=manager,
                start_date = data.get('start_date'),
                end_date = data.get('end_date'),
            )

            # -------------------------------------------------
            # Creator becomes OWNER
            # -------------------------------------------------
            ProjectMember.objects.create(
                project=project,
                user=request.user,
                role='OWNER'
            )

            # -------------------------------------------------
            # Team members (optional)
            # -------------------------------------------------
            team_members = data.get('team_members', [])

            for member in team_members:
                user_id = member.get('user_id')
                role = member.get('role', 'MEMBER')

                user = User.objects.filter(id=user_id).first()
                employee = Employee.objects.filter(
                    user=user,
                    company=company
                ).first()

                if not user or not employee:
                    continue

                ProjectMember.objects.update_or_create(
                    project=project,
                    user=user,
                    defaults={
                        'role': role,
                        'is_active': True
                    }
                )

            # -------------------------------------------------
            # DEFAULT WORKFLOW (UNCHANGED)
            # -------------------------------------------------
            workflow = Workflow.objects.create(
                project=project,
                name='Default Workflow'
            )

            todo = WorkflowStatus.objects.create(workflow=workflow, key='TODO', label='To Do', order=1)
            in_progress = WorkflowStatus.objects.create(workflow=workflow, key='IN_PROGRESS', label='In Progress', order=2)
            in_review = WorkflowStatus.objects.create(workflow=workflow, key='IN_REVIEW', label='In Review', order=3)
            done = WorkflowStatus.objects.create(workflow=workflow, key='DONE', label='Done', order=4, is_terminal=True)

            WorkflowTransition.objects.bulk_create([
                WorkflowTransition(workflow=workflow, from_status=todo, to_status=in_progress,
                                   allowed_roles=['OWNER', 'MANAGER', 'MEMBER']),
                WorkflowTransition(workflow=workflow, from_status=in_progress, to_status=in_review,
                                   allowed_roles=['OWNER', 'MANAGER'], require_assignee=True),
                WorkflowTransition(workflow=workflow, from_status=in_review, to_status=done,
                                   allowed_roles=['OWNER', 'MANAGER'], require_comment=True),
            ])

            return Response({
                'status': True,
                'records': {
                    'id': str(project.id),
                    'name': project.name
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# Project List
# ------------------------------------------------------------------
class ProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            search_data = request.data
            page = int(search_data.get('page', 1))
            page_size = int(search_data.get('page_size', 10))
            search_project = search_data.get('search', '').strip()

            # 🔐 restrict to member projects
            project_ids = ProjectMember.objects.filter(
                user=request.user,
                is_active=True
            ).values_list('project_id', flat=True)

            projects_queryset = Project.objects.select_related(
                'manager__user'
            ).filter(id__in=project_ids)

            query = Q()
            if search_project:
                query &= (
                    Q(name__icontains=search_project) |
                    Q(description__icontains=search_project) |
                    Q(manager__user__name__icontains=search_project) |
                    Q(manager__user__email__icontains=search_project)
                )

            projects = projects_queryset.filter(query).order_by('-created_at')

            if not projects.exists():
                return Response({
                    'status': False,
                    'message': 'Projects not found',
                    'count': 0,
                    'records': []
                }, status=status.HTTP_200_OK)

            paginator = Paginator(projects, page_size)
            try:
                paginated_projects = paginator.page(page)
            except Exception:
                paginated_projects = paginator.page(1)

            project_data = []
            for project in paginated_projects:

                active_sprint = Sprint.objects.filter(
                    project=project,
                    status__in=['ACTIVE', 'PLANNED', 'COMPLETED'],
                    deleted_at__isnull=True
                ).first()

                project_data.append({
                    'id': str(project.id),
                    'name': project.name,
                    'description': project.description,
                    'status': project.status,
                    'manager': {
                        'id': str(project.manager.id) if project.manager else None,
                        'user_id': str(project.manager.user.id) if project.manager and project.manager.user else None,
                        'name': project.manager.user.name if project.manager and project.manager.user else None,
                        'email': project.manager.user.email if project.manager and project.manager.user else None,
                        'username': project.manager.user.username if project.manager and project.manager.user else None
                    } if project.manager else None,
                    # ---- ✅ NEW FIELD (ADD ONLY) ----
                    'sprint_info': {
                        'has_active_sprint': True if active_sprint else False,
                        'active_sprint_id': str(active_sprint.id) if active_sprint else None,
                        'active_sprint_name': active_sprint.name if active_sprint else None
                    },
                    'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': project.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            return Response({
                'status': True,
                'count': paginator.count,
                'num_pages': paginator.num_pages,
                'current_page': page,
                'records': project_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ------------------------------------------------------------------
# Deleted Project List
# ------------------------------------------------------------------
class DeletedProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # 🔐 only OWNER projects
            owned_ids = ProjectMember.objects.filter(
                user=request.user,
                role='OWNER',
                is_active=True
            ).values_list('project_id', flat=True)

            projects = Project.all_objects.filter(
                id__in=owned_ids,
                deleted_at__isnull=False
            ).order_by('-created_at')

            if not projects.exists():
                return Response({
                    'status': False,
                    'message': 'Deleted projects not found',
                }, status=status.HTTP_200_OK)

            serializer = ProjectSerializer(projects, many=True)
            return Response({
                'status': True,
                'count': projects.count(),
                'records': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ------------------------------------------------------------------
# Project Details
# ------------------------------------------------------------------
class ProjectDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        try:
            project = Project.objects.select_related('manager').filter(id=id).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            require_project_viewer(request.user, project)

            # ---------------- Team members ----------------
            members = ProjectMember.objects.filter(
                project=project,
                is_active=True
            ).select_related('user')

            team_data = [{
                'user': {
                    'id': str(m.user.id),
                    'name': m.user.name,
                    'email': m.user.email
                },
                'role': m.role
            } for m in members]

            # ---------------- Files ----------------
            files = ProjectFile.objects.filter(project=project)

            file_data = [{
                'id': str(f.id),
                'name': f.original_name,
                'url': f.file_url,
                'uploaded_at': f.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
            } for f in files]

            # ---------------- Response ----------------
            data = {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'manager_id': project.manager.id if project.manager else None,
                'manager_name': project.manager.user.name if project.manager else None,
                'start_date': project.start_date,
                'end_date': project.end_date,
                'status': project.status,
                'team_members': team_data,
                'files': file_data
            }

            return Response(
                {'status': True, 'records': data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        



# ------------------------------------------------------------------
# Project Update
# ------------------------------------------------------------------
class ProjectUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            project = Project.objects.filter(id=request.data.get('id')).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            require_project_manager_or_hr(request.user, project)

            employee = Employee.objects.filter(user=request.user).first()
            company = employee.company

            # ---------------- Manager ----------------
            manager_id = request.data.get('manager_id')
            if manager_id:
                manager = Employee.objects.filter(
                    id=manager_id,
                    company=company
                ).first()
                project.manager = manager

            # ---------------- Basic fields ----------------
            if 'name' in request.data:
                project.name = request.data.get('name')

            if 'description' in request.data:
                project.description = request.data.get('description')

            if 'start_date' in request.data:
                project.start_date = request.data.get('start_date')

            if 'end_date' in request.data:
                project.end_date = request.data.get('end_date')

            project.updated_by = request.user
            project.save()

            # ---------------- Team update ----------------
            incoming = request.data.get('team_members', [])
            incoming_user_ids = []

            for member in incoming:
                user_id = member.get('user_id')
                role = member.get('role', 'MEMBER')
                user = User.objects.filter(id=user_id).first()

                if not user:
                    continue

                incoming_user_ids.append(user.id)

                ProjectMember.objects.update_or_create(
                    project=project,
                    user=user,
                    defaults={
                        'role': role,
                        'is_active': True
                    }
                )

            # deactivate removed members (except OWNER)
            ProjectMember.objects.filter(
                project=project
            ).exclude(
                user__id__in=incoming_user_ids
            ).exclude(
                role='OWNER'
            ).update(is_active=False)

            return Response(
                {
                    'status': True,
                    'message': 'Project updated successfully'
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )




# ------------------------------------------------------------------
# Project Delete
# ------------------------------------------------------------------
class ProjectDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, project_id):
        try:
            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_200_OK)

            require_project_owner(request.user, project)

            project.soft_delete()
            return Response({'status': True, 'message': 'Project deleted successfully'},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ------------------------------------------------------------------
# Restore Project
# ------------------------------------------------------------------
class RestoreProject(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.all_objects.filter(id=request.data.get('id')).first()
            if not project:
                return Response({'status': False, 'message': 'Project not found'}, status=status.HTTP_200_OK)

            require_project_owner(request.user, project)

            project.deleted_at = None
            project.save()

            return Response({'status': True, 'message': 'Project restored successfully'},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ------------------------------------------------------------------
# Project Summary
# ------------------------------------------------------------------
class ProjectSummary(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        search = request.data.get('search', '').strip()
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 5))

        project_ids = ProjectMember.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('project_id', flat=True)

        qs = Project.objects.filter(id__in=project_ids, deleted_at__isnull=True)

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(team_name__icontains=search) |
                Q(manager__user__name__icontains=search)
            )

        total = qs.count()
        qs = qs.order_by('-created_at')[(page-1)*page_size: page*page_size]

        serializer = ProjectSerializer(qs, many=True)
        return Response({'records': serializer.data, 'count': total})

# ------------------------------------------------------------------
# Remaining APIs (ManagerProjects, AssignProjectManager, EmployeeProjectList,
# ProjectTasksList, ProjectMilestonesList, ManagerProjectList,
# UploadProjectFiles, ProjectFilesList, GenerateProjectInvoice, ProjectUsers)
# ------------------------------------------------------------------
# 🔐 All of these ALREADY had require_project_viewer / manager checks
# added earlier and remain unchanged in behavior.


class ManagerProjects(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            projects = Project.objects.filter(
                manager=request.user,
                deleted_at__isnull=True
            ).values(
                'id', 'name', 'status', 'created_at', 'updated_at'
            )

            return Response({
                'status': True,
                'records': list(projects)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class AssignProjectManager(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(
                id=request.data.get('project_id')
            ).first()

            if not project:
                return Response({'status': False, 'message': 'Project not found'},
                                status=status.HTTP_200_OK)

            require_project_owner(request.user, project)

            manager_id = request.data.get('manager_id')
            if not manager_id:
                return Response({'status': False, 'message': 'manager_id is required'},
                                status=status.HTTP_400_BAD_REQUEST)

            project.manager_id = manager_id
            project.save(update_fields=['manager'])

            return Response({
                'status': True,
                'message': 'Project manager assigned successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class EmployeeProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_ids = ProjectMember.objects.filter(
                user=request.user,
                deleted_at__isnull=True
            ).values_list('project_id', flat=True)

            projects = Project.objects.filter(
                id__in=project_ids,
                deleted_at__isnull=True
            ).values(
                'id', 'name', 'status', 'created_at'
            )

            return Response({
                'status': True,
                'records': list(projects)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class ProjectTasksList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(
                id=request.data.get('project_id')
            ).first()

            if not project:
                return Response({'status': False, 'message': 'Project not found'},
                                status=status.HTTP_200_OK)

            require_project_viewer(request.user, project)

            tasks = Task.objects.filter(
                project=project,
                deleted_at__isnull=True
            ).order_by('order').values(
                'id',
                'title',
                'status',
                'priority',
                'assigned_to_id',
                'sprint_id',
                'order',
                'created_at'
            )

            return Response({
                'status': True,
                'records': list(tasks)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

class ProjectMilestonesList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(
                id=request.data.get('project_id')
            ).first()

            if not project:
                return Response({'status': False, 'message': 'Project not found'},
                                status=status.HTTP_200_OK)

            require_project_viewer(request.user, project)

            epics = Epic.objects.filter(
                project=project,
                deleted_at__isnull=True
            ).values(
                'id',
                'name',
                'status',
                'start_date',
                'end_date'
            )

            return Response({
                'status': True,
                'records': list(epics)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

class ManagerProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            projects = Project.objects.filter(
                manager=request.user,
                deleted_at__isnull=True
            ).values(
                'id', 'name', 'status'
            )

            return Response({
                'status': True,
                'records': list(projects)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)





class GenerateProjectInvoice(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(
                id=request.data.get('project_id')
            ).first()

            if not project:
                return Response({'status': False, 'message': 'Project not found'},
                                status=status.HTTP_200_OK)

            require_project_manager(request.user, project)

            return Response({
                'status': True,
                'message': 'Invoice generated successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


class ProjectUsers(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(
                id=request.data.get('project_id')
            ).first()

            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_200_OK
                )

            # 🔐 Viewer access is enough
            require_project_viewer(request.user, project)

            # ✅ ProjectMember uses is_active (NOT deleted_at)
            members = ProjectMember.objects.filter(
                project=project,
                is_active=True
            ).select_related('user')

            records = [
                {
                    'user_id': m.user.id,
                    'name': m.user.name,
                    'role': m.role
                }
                for m in members
            ]

            return Response(
                {'status': True, 'records': records},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
