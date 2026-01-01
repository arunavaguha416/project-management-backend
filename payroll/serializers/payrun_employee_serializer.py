from rest_framework import serializers
from payroll.models.payroll_models import Payroll
from hr_management.models.hr_management_models import Employee
from department.models.department_model import Department

class PayRunEmployeeSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = [
            "id",
            "employee_name",
            "department",
            "payable_days",
            "lop_days",
            "overtime_hours",
            "gross_salary",
            "total_deductions",
            "net_salary",
            "status"
        ]

    def get_employee_name(self, obj):
        if obj.employee and obj.employee.user:
            return obj.employee.user.name
        return "-"

    def get_department(self, obj):
        if not obj.employee or not obj.employee.user:
            return "-"

        mapping = Department.objects.filter(
            id=obj.employee.department.id,
            deleted_at__isnull=True
        ).select_related("department").first()

        if mapping and mapping.department:
            return mapping.department.name

        return "-"
