# payroll/serializers/payroll_serializer.py
from rest_framework import serializers
from payroll.models.payroll_models import *
from hr_management.models.hr_management_models import Employee
from time_tracking.models.time_tracking_models import TimeEntry
from decimal import Decimal

class PayrollPeriodSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'start_date', 'end_date', 'period_name', 'status',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PayRunSerializer(serializers.ModelSerializer):
    payroll_period_name = serializers.CharField(
        source='payroll_period.period_name', read_only=True
    )

    class Meta:
        model = PayRun
        fields = [
            'id',
            'payroll_period',
            'payroll_period_name',
            'status',
            'total_employees',
            'total_gross_salary',
            'total_deductions',
            'total_net_salary',
            'created_at'
        ]

class PayRunEmployeeSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name')
    status = serializers.CharField()

    class Meta:
        model = Payroll
        fields = [
            'id',
            'employee_name',
            'basic_salary',
            'total_allowances',
            'total_deductions',
            'net_salary',
            'status'
        ]


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.name', read_only=True)
    employee_email = serializers.CharField(source='employee.user.email', read_only=True)
    employee_designation = serializers.CharField(source='employee.designation', read_only=True)
    period_name = serializers.CharField(source='payroll_period.period_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True)
    
    # overtime_hours_from_timesheet = serializers.SerializerMethodField()
    # attendance_percentage = serializers.SerializerMethodField()
    
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = Payroll
        fields = [
            'id', 'employee', 'employee_name', 'employee_email', 'employee_designation',
            'payroll_period', 'period_name', 'basic_salary', 
            # 'overtime_hours', 'overtime_rate', 'overtime_amount', 
            'house_rent_allowance', 
            'transport_allowance', 
            # 'medical_allowance', 
            'other_allowances',
            # 'performance_bonus', 'attendance_bonus', 'project_bonus',
            'provident_fund', 'professional_tax', 'income_tax', 
            # 'health_insurance', 'other_deductions', 
            'gross_salary',
            'total_deductions', 'net_salary', 'status',
            'processed_by', 'processed_by_name', 'approved_by', 'approved_by_name',
            # 'overtime_hours_from_timesheet', 'attendance_percentage',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = [
            'id', 
            # 'overtime_rate', 'overtime_amount', 
            'gross_salary', 
            'total_deductions', 'net_salary', 'created_at', 'updated_at'
        ]

    # def get_overtime_hours_from_timesheet(self, obj):
    #     """Calculate overtime hours from time tracking data"""
    #     try:
    #         time_entries = TimeEntry.objects.filter(
    #             user=obj.employee.user,
    #             date__range=[obj.payroll_period.start_date, obj.payroll_period.end_date],
    #             duration__isnull=False
    #         )
            
    #         total_hours = sum([
    #             entry.duration.total_seconds() / 3600 
    #             for entry in time_entries
    #         ])
            
    #         # Standard working hours per month (assuming 22 working days * 8 hours)
    #         standard_hours = 176
    #         overtime_hours = max(0, total_hours - standard_hours)
            
    #         return round(overtime_hours, 2)
    #     except:
    #         return 0.0

    def get_attendance_percentage(self, obj):
        """Calculate attendance percentage from time tracking"""
        try:
            total_working_days = 22  # Standard working days per month
            time_entries = TimeEntry.objects.filter(
                user=obj.employee.user,
                date__range=[obj.payroll_period.start_date, obj.payroll_period.end_date],
                login_time__isnull=False
            ).count()
            
            return round((time_entries / total_working_days) * 100, 2)
        except:
            return 0.0

class PayrollSummarySerializer(serializers.Serializer):
    total_employees = serializers.IntegerField()
    total_gross_salary = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_deductions = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_net_salary = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_overtime_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_bonuses = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_attendance = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
