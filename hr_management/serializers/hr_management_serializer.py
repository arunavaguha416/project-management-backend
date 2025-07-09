from rest_framework import serializers
from hr_management.models.hr_management_models import LeaveRequest,Employee

class LeaveRequestSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_id', 'start_date', 'end_date', 'reason', 'status',
            'created_at', 'updated_at', 'deleted_at', 'published_at'
        ]

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [ 
            'id', 'user_id', 'comp_id', 'dept_id'
        ]

        