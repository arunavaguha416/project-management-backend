from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from projects.models.project_model import Project
from projects.models.sprint_model import Sprint
from projects.utils.permissions import (
    require_project_manager,
    require_project_owner,
    require_project_manager_or_hr
)
from django.utils import timezone

# ---------------------------------------------------------
# Sprint Settings – Details (READ)
# ---------------------------------------------------------
class SprintSettingsDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")
            sprint = Sprint.objects.select_related("project").filter(
                id=sprint_id,
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            # 🔐 Manager access required
            require_project_manager(request.user, sprint.project)

            return Response({
                "status": True,
                "records": {
                    "id": str(sprint.id),
                    "name": sprint.name,
                    "goal": sprint.goal,
                    "start_date": sprint.start_date,
                    "end_date": sprint.end_date,
                    "status": sprint.status,
                    "velocity": sprint.velocity,
                    "created_at": sprint.created_at,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Sprint Settings – Update (WRITE)
# ---------------------------------------------------------
class SprintSettingsUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        try:
            sprint = Sprint.objects.select_related("project").filter(
                id=request.data.get("id"),
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            require_project_manager(request.user, sprint.project)

            sprint.name = request.data.get("name", sprint.name)
            sprint.goal = request.data.get("goal", sprint.goal)
            sprint.start_date = request.data.get("start_date", sprint.start_date)
            sprint.end_date = request.data.get("end_date", sprint.end_date)
            sprint.capacity = request.data.get("capacity", sprint.capacity)

            sprint.save()

            return Response(
                {"status": True, "message": "Sprint settings updated"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Sprint Settings – Start Sprint
# ---------------------------------------------------------
class SprintStart(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")
            today = timezone.now().date()
            if not sprint_id:
                return Response(
                    {"status": False, "message": "sprint_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            sprint = Sprint.objects.select_related("project").filter(
                id=sprint_id,
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            project = sprint.project

            # 🔒 Permission
            require_project_manager_or_hr(request.user, project)

            if sprint.status != "PLANNED":
                return Response(
                    {"status": False, "message": "Sprint is not in PLANNED state"},
                    status=status.HTTP_200_OK
                )

            # 🔥 Close any existing ACTIVE sprint
            Sprint.objects.filter(
                project=project,
                status="ACTIVE"
            ).exclude(id=sprint.id).update(
                status="COMPLETED",
                end_date= today
            )
            
            # 🔥 Activate this sprint
            sprint.status = "ACTIVE"
            sprint.start_date =  today
            sprint.save()

            # 🔥 Update project status
            project.status = Project.projectStatus.ONGOING
            project.updated_by = request.user
            project.save(update_fields=["status", "updated_by", "updated_at"])

            return Response(
                {
                    "status": True,
                    "message": "Sprint started successfully",
                    "records": {
                        "sprint_id": str(sprint.id),
                        "project_id": str(project.id)
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Sprint Settings – Complete Sprint
# ---------------------------------------------------------
class SprintComplete(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint = Sprint.objects.select_related("project").filter(
                id=request.data.get("sprint_id"),
                deleted_at__isnull=True
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            require_project_manager(request.user, sprint.project)

            sprint.status = "COMPLETED"
            sprint.save()

            return Response(
                {"status": True, "message": "Sprint completed"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Sprint Settings – Delete Sprint (OWNER)
# ---------------------------------------------------------
class SprintDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            sprint_id = request.data.get("sprint_id")

            sprint = Sprint.objects.select_related("project").filter(
                id=sprint_id
            ).first()

            if not sprint:
                return Response(
                    {"status": False, "message": "Sprint not found"},
                    status=status.HTTP_200_OK
                )

            # 🔐 OWNER only
            require_project_owner(request.user, sprint.project)

            sprint.soft_delete()

            return Response(
                {"status": True, "message": "Sprint deleted"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Sprint Settings – Create Sprint (OWNER)
# ---------------------------------------------------------
class SprintCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get("project_id")
            name = request.data.get("name", "Sprint Planning")
            sprint_status = request.data.get("status", "PLANNED")

            if not project_id:
                return Response(
                    {"status": False, "message": "project_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            project = Project.objects.filter(
                id=project_id,
                deleted_at__isnull=True
            ).first()

            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 🔐 Permission: Manager / Owner / HR
            require_project_manager_or_hr(request.user, project)

            # 🚫 Prevent multiple active/planned sprints if needed (optional)
            existing = Sprint.objects.filter(
                project=project,
                status__in=['ACTIVE', 'PLANNED', 'COMPLETED'],
                deleted_at__isnull=True
            ).first()

            if existing:
                return Response({
                    "status": True,
                    "records": {
                        "sprint_id": str(existing.id)
                    }
                }, status=status.HTTP_200_OK)

            # 🆕 Create draft sprint
            sprint = Sprint.objects.create(
                project=project,
                name=name,
                status=sprint_status
            )

            return Response({
                "status": True,
                "records": {
                    "sprint_id": str(sprint.id)
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )