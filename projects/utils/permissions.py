from rest_framework.exceptions import PermissionDenied
from projects.models.project_model import Project
from projects.models.project_member_model import ProjectMember

ROLE_OWNER = 'OWNER'
ROLE_MANAGER = 'MANAGER'
ROLE_MEMBER = 'MEMBER'
ROLE_VIEWER = 'VIEWER'

def get_project_member(user, project: Project):
    if not user or not project:
        return None
    return ProjectMember.objects.filter(
        user=user,
        project=project,
        is_active=True
    ).first()

def get_project_role(user, project: Project):
    member = get_project_member(user, project)
    return member.role if member else None

def require_project_role(user, project: Project, allowed_roles: list):
    role = get_project_role(user, project)

    # 🔒 explicit membership guard (VERY IMPORTANT)
    if role is None:
        raise PermissionDenied("You are not a member of this project")

    if role not in allowed_roles:
        raise PermissionDenied(
            f"Action not allowed for project role: {role}"
        )

def require_project_owner(user, project: Project):
    require_project_role(user, project, [ROLE_OWNER])

def require_project_manager(user, project: Project):
    require_project_role(user, project, [ROLE_OWNER, ROLE_MANAGER])

def require_project_editor(user, project: Project):
    require_project_role(user, project, [ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER])

def require_project_viewer(user, project: Project):
    require_project_role(user, project, [
        ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER, ROLE_VIEWER
    ])
