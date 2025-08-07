from rest_framework import serializers
from hr_management.models.hr_management_models import *
from authentication.serializers.serializer import UserSerializer


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ["balance"]
class LeaveRequestSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta(object):
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_id', 'start_date', 'end_date', 'reason', 'status'           
        ]

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Employee
        fields = [ 
            'id','user', 'user_id', 'company_id', 'department_id','salary','date_of_joining','designation'
        ]

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['date', 'in_time', 'out_time']

        