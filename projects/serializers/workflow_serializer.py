from rest_framework import serializers
from projects.models.workflow_model import (
    Workflow,
    WorkflowStatus,
    WorkflowTransition
)


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'is_active', 'created_at']


class WorkflowStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStatus
        fields = [
            'id',
            'key',
            'label',
            'order',
            'is_terminal'
        ]


class WorkflowTransitionSerializer(serializers.ModelSerializer):
    from_status_key = serializers.CharField(source='from_status.key', read_only=True)
    to_status_key = serializers.CharField(source='to_status.key', read_only=True)

    class Meta:
        model = WorkflowTransition
        fields = [
            'id',
            'from_status',
            'to_status',
            'from_status_key',
            'to_status_key',
            'allowed_roles',
            'require_assignee',
            'require_comment'
        ]
