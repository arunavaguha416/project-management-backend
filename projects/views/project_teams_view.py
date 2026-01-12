from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from authentication.models.user import User
from projects.models.project_model import Project
from projects.models.project_member_model import ProjectMember
from projects.utils.permissions import (
    require_project_viewer,
    require_project_owner,
)

# ---------------------------------------------------------
# List Project Team
# ---------------------------------------------------------
class ProjectTeamList(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get("project_id")
            if not project_id:
                return Response(
                    {"status": False, "message": "project_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=status.HTTP_200_OK
                )

            # 🔐 Viewer access (unchanged)
            require_project_viewer(request.user, project)

            members_qs = (
                ProjectMember.objects
                .filter(project=project, is_active=True)
                .select_related("user")
                .order_by("role", "joined_at")
            )

            records = []
            can_manage = False

            for m in members_qs:
                # 🔑 Check role of CURRENT USER
                if m.user_id == request.user.id and m.role in ["OWNER", "MANAGER"]:
                    can_manage = True
                
                owner_count = ProjectMember.objects.filter(
                    project=project,
                    role="OWNER",
                    is_active=True
                ).count()


                records.append({
                    "id": str(m.id),
                    "user": {
                        "id": str(m.user.id),
                        "name": m.user.name,
                        "email": m.user.email,
                    },
                    "role": m.role,
                    "joined_at": m.joined_at,
                    "is_last_owner": m.role == "OWNER" and owner_count == 1
                })


            return Response(
                {
                    "status": True,
                    "records": records,
                    "can_manage": can_manage,               # ✅ REQUIRED
                    "current_user_id": str(request.user.id) # ✅ REQUIRED
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



# ---------------------------------------------------------
# Add Member to Project
# ---------------------------------------------------------
class ProjectTeamAdd(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project_id = request.data.get("project_id")
            user_id = request.data.get("user_id")
            role = request.data.get("role", "MEMBER")

            if not project_id or not user_id:
                return Response(
                    {"status": False, "message": "project_id and user_id are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            project = Project.objects.filter(id=project_id).first()
            if not project:
                return Response(
                    {"status": False, "message": "Project not found"},
                    status=status.HTTP_200_OK
                )

            require_project_owner(request.user, project)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {"status": False, "message": "User not found"},
                    status=status.HTTP_200_OK
                )

            member, created = ProjectMember.objects.get_or_create(
                project=project,
                user=user,
                defaults={"role": role, "is_active": True}
            )

            if not created:
                if member.is_active:
                    return Response(
                        {"status": False, "message": "User already in project"},
                        status=status.HTTP_200_OK
                    )
                member.is_active = True
                member.role = role
                member.save()

            return Response(
                {"status": True, "message": "Member added to project"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Update Member Role
# ---------------------------------------------------------
class ProjectTeamUpdateRole(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            member_id = request.data.get("member_id")
            role = request.data.get("role")

            if not member_id or not role:
                return Response(
                    {"status": False, "message": "member_id and role are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            member = ProjectMember.objects.select_related(
                "project", "user"
            ).filter(id=member_id, is_active=True).first()

            if not member:
                return Response(
                    {"status": False, "message": "Member not found"},
                    status=status.HTTP_200_OK
                )

            require_project_owner(request.user, member.project)

            # 🔒 Prevent removing last OWNER
            if member.role == "OWNER" and role != "OWNER":
                owner_count = ProjectMember.objects.filter(
                    project=member.project,
                    role="OWNER",
                    is_active=True
                ).count()
                if owner_count <= 1:
                    return Response(
                        {"status": False, "message": "Project must have at least one OWNER"},
                        status=status.HTTP_200_OK
                    )

            member.role = role
            member.save(update_fields=["role"])

            return Response(
                {"status": True, "message": "Role updated successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Remove Member (Soft)
# ---------------------------------------------------------
class ProjectTeamRemove(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            member_id = request.data.get("member_id")

            if not member_id:
                return Response(
                    {"status": False, "message": "member_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            member = ProjectMember.objects.select_related(
                "project", "user"
            ).filter(id=member_id, is_active=True).first()

            if not member:
                return Response(
                    {"status": False, "message": "Member not found"},
                    status=status.HTTP_200_OK
                )

            require_project_owner(request.user, member.project)

            if member.user == request.user:
                return Response(
                    {"status": False, "message": "You cannot remove yourself"},
                    status=status.HTTP_200_OK
                )

            # 🔒 Prevent removing last OWNER
            if member.role == "OWNER":
                owner_count = ProjectMember.objects.filter(
                    project=member.project,
                    role="OWNER",
                    is_active=True
                ).count()
                if owner_count <= 1:
                    return Response(
                        {"status": False, "message": "Project must have at least one OWNER"},
                        status=status.HTTP_200_OK
                    )

            member.is_active = False
            member.save(update_fields=["is_active"])

            return Response(
                {"status": True, "message": "Member removed from project"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
