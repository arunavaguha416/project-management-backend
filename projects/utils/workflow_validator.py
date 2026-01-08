from rest_framework.exceptions import ValidationError, PermissionDenied
from projects.models.workflow_model import WorkflowTransition
from projects.utils.permissions import get_project_role


def validate_task_transition(*, task, new_status, user):
    project = task.project
    workflow = getattr(project, 'workflow', None)

    if not workflow or not workflow.is_active:
        return  # No workflow = allow (backward compatibility)

    current_status = task.status

    transition = WorkflowTransition.objects.filter(
        workflow=workflow,
        from_status__key=current_status,
        to_status__key=new_status
    ).select_related('from_status', 'to_status').first()

    if not transition:
        raise ValidationError(
            f"Transition from {current_status} to {new_status} is not allowed"
        )

    role = get_project_role(user, project)
    if role not in transition.allowed_roles:
        raise PermissionDenied(
            f"Role {role} is not allowed to move task to {new_status}"
        )

    if transition.require_assignee and not task.assigned_to:
        raise ValidationError("Task must be assigned before this transition")

    if transition.require_comment:
        # You already have comments model
        if not task.comments.exists():
            raise ValidationError("Comment is required for this transition")
