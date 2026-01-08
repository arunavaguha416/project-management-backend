from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from projects.models.project_model import Project
from projects.models.workflow_model import (
    Workflow,
    WorkflowStatus,
    WorkflowTransition
)
from projects.utils.permissions import (
    require_project_owner,
)

# ---------------------------------------------------------
# Helper: owner OR global admin
# ---------------------------------------------------------
def require_workflow_admin(user, project):
    if user.role == 'ADMIN':
        return
    require_project_owner(user, project)


# ---------------------------------------------------------
# Get Workflow (Project-level)
# ---------------------------------------------------------
class WorkflowDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(id=request.data.get('project_id')).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_200_OK
                )

            require_workflow_admin(request.user, project)

            workflow = getattr(project, 'workflow', None)
            if not workflow:
                return Response(
                    {'status': False, 'message': 'Workflow not found'},
                    status=status.HTTP_200_OK
                )

            statuses = WorkflowStatus.objects.filter(
                workflow=workflow
            ).order_by('order')

            transitions = WorkflowTransition.objects.filter(
                workflow=workflow
            )

            return Response({
                'status': True,
                'records': {
                    'workflow': {
                        'id': str(workflow.id),
                        'name': workflow.name,
                        'is_active': workflow.is_active
                    },
                    'statuses': [
                        {
                            'id': str(s.id),
                            'key': s.key,
                            'label': s.label,
                            'order': s.order,
                            'is_terminal': s.is_terminal
                        } for s in statuses
                    ],
                    'transitions': [
                        {
                            'id': str(t.id),
                            'from_status': t.from_status.key,
                            'to_status': t.to_status.key,
                            'allowed_roles': t.allowed_roles,
                            'require_assignee': t.require_assignee,
                            'require_comment': t.require_comment
                        } for t in transitions
                    ]
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Add / Update Workflow Status
# ---------------------------------------------------------
class WorkflowStatusUpsert(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(id=request.data.get('project_id')).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_200_OK
                )

            require_workflow_admin(request.user, project)

            workflow = project.workflow

            status_id = request.data.get('id')
            if status_id:
                status_obj = WorkflowStatus.objects.filter(
                    id=status_id, workflow=workflow
                ).first()
                if not status_obj:
                    return Response(
                        {'status': False, 'message': 'Status not found'},
                        status=status.HTTP_200_OK
                    )
            else:
                status_obj = WorkflowStatus(workflow=workflow)

            status_obj.key = request.data.get('key')
            status_obj.label = request.data.get('label')
            status_obj.order = request.data.get('order', 0)
            status_obj.is_terminal = request.data.get('is_terminal', False)
            status_obj.save()

            return Response(
                {'status': True, 'message': 'Workflow status saved successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Delete Workflow Status
# ---------------------------------------------------------
class WorkflowStatusDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, status_id):
        try:
            status_obj = WorkflowStatus.objects.select_related(
                'workflow__project'
            ).filter(id=status_id).first()

            if not status_obj:
                return Response(
                    {'status': False, 'message': 'Status not found'},
                    status=status.HTTP_200_OK
                )

            require_workflow_admin(request.user, status_obj.workflow.project)

            status_obj.delete()
            return Response(
                {'status': True, 'message': 'Workflow status deleted successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Add / Update Workflow Transition
# ---------------------------------------------------------
class WorkflowTransitionUpsert(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            project = Project.objects.filter(id=request.data.get('project_id')).first()
            if not project:
                return Response(
                    {'status': False, 'message': 'Project not found'},
                    status=status.HTTP_200_OK
                )

            require_workflow_admin(request.user, project)

            workflow = project.workflow

            transition_id = request.data.get('id')
            if transition_id:
                transition = WorkflowTransition.objects.filter(
                    id=transition_id, workflow=workflow
                ).first()
                if not transition:
                    return Response(
                        {'status': False, 'message': 'Transition not found'},
                        status=status.HTTP_200_OK
                    )
            else:
                transition = WorkflowTransition(workflow=workflow)

            from_status = WorkflowStatus.objects.filter(
                workflow=workflow,
                key=request.data.get('from_status')
            ).first()
            to_status = WorkflowStatus.objects.filter(
                workflow=workflow,
                key=request.data.get('to_status')
            ).first()

            if not from_status or not to_status:
                return Response(
                    {'status': False, 'message': 'Invalid from/to status'},
                    status=status.HTTP_200_OK
                )

            transition.from_status = from_status
            transition.to_status = to_status
            transition.allowed_roles = request.data.get('allowed_roles', [])
            transition.require_assignee = request.data.get('require_assignee', False)
            transition.require_comment = request.data.get('require_comment', False)
            transition.save()

            return Response(
                {'status': True, 'message': 'Workflow transition saved successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ---------------------------------------------------------
# Delete Workflow Transition
# ---------------------------------------------------------
class WorkflowTransitionDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, transition_id):
        try:
            transition = WorkflowTransition.objects.select_related(
                'workflow__project'
            ).filter(id=transition_id).first()

            if not transition:
                return Response(
                    {'status': False, 'message': 'Transition not found'},
                    status=status.HTTP_200_OK
                )

            require_workflow_admin(request.user, transition.workflow.project)

            transition.delete()
            return Response(
                {'status': True, 'message': 'Workflow transition deleted successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'status': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
