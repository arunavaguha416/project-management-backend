from rest_framework import serializers
from payroll.models.loan_models import LoanAdvance


class LoanAdvanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.name', read_only=True)
    employee_email = serializers.CharField(source='employee.user.email', read_only=True)
    employee_designation = serializers.CharField(source='employee.designation', read_only=True)
    balance_ratio = serializers.SerializerMethodField()

    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()

    class Meta:
        model = LoanAdvance
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_email',
            'employee_designation',
            'loan_type',
            'principal_amount',
            'emi_amount',
            'outstanding_balance',
            'tenure_months',
            'disbursed_date',
            'next_deduction_date',
            'status',
            'notes',
            'balance_ratio',
            'created_at',
            'updated_at',
            'deleted_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_balance_ratio(self, obj):
        principal = float(obj.principal_amount or 0)
        balance = float(obj.outstanding_balance or 0)
        if principal <= 0:
            return 0
        return round((balance / principal) * 100, 2)
