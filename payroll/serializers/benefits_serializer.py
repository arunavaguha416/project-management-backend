# payroll/serializers/benefits_serializer.py
from rest_framework import serializers
from payroll.models.benefits_models import BenefitPlan, BenefitEnrollment, TaxConfiguration

class BenefitPlanSerializer(serializers.ModelSerializer):
    enrolled_employees_count = serializers.SerializerMethodField()
    is_enrollment_open = serializers.SerializerMethodField()
    days_until_enrollment_ends = serializers.SerializerMethodField()
    
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = BenefitPlan
        fields = [
            'id', 'name', 'description', 'plan_type', 'provider',
            'coverage_amount', 'employee_contribution', 'employer_contribution',
            'is_mandatory', 'eligibility_criteria', 'waiting_period_days',
            'enrollment_start_date', 'enrollment_end_date', 
            'plan_year_start', 'plan_year_end', 'is_active',
            'enrolled_employees_count', 'is_enrollment_open', 'days_until_enrollment_ends',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_enrolled_employees_count(self, obj):
        return BenefitEnrollment.objects.filter(
            benefit_plan=obj, 
            status='Active'
        ).count()

    def get_is_enrollment_open(self, obj):
        from datetime import date
        today = date.today()
        return obj.enrollment_start_date <= today <= obj.enrollment_end_date

    def get_days_until_enrollment_ends(self, obj):
        from datetime import date
        today = date.today()
        if obj.enrollment_end_date >= today:
            return (obj.enrollment_end_date - today).days
        return 0

class BenefitEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.name', read_only=True)
    employee_email = serializers.CharField(source='employee.user.email', read_only=True)
    plan_name = serializers.CharField(source='benefit_plan.name', read_only=True)
    plan_type = serializers.CharField(source='benefit_plan.plan_type', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True)
    
    annual_employee_cost = serializers.SerializerMethodField()
    annual_employer_cost = serializers.SerializerMethodField()
    
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = BenefitEnrollment
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'benefit_plan', 'plan_name', 'plan_type', 'enrollment_date',
            'effective_date', 'end_date', 'coverage_level',
            'spouse_covered', 'children_count', 'employee_monthly_cost',
            'employer_monthly_cost', 'annual_employee_cost', 'annual_employer_cost',
            'status', 'submitted_by', 'submitted_by_name', 
            'approved_by', 'approved_by_name', 'approved_at',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = [
            'id', 'approved_at', 'created_at', 'updated_at'
        ]

    def get_annual_employee_cost(self, obj):
        return obj.employee_monthly_cost * 12

    def get_annual_employer_cost(self, obj):
        return obj.employer_monthly_cost * 12

class TaxConfigurationSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = TaxConfiguration
        fields = [
            'id', 'country', 'state', 'tax_year', 'tax_slabs',
            'standard_deduction', 'professional_tax_rate', 'provident_fund_rate',
            'cess_rate', 'surcharge_threshold', 'surcharge_rate',
            'is_active', 'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
