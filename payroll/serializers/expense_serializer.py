# payroll/serializers/expense_serializer.py
from rest_framework import serializers
from payroll.models.expense_models import ExpenseCategory, ExpenseClaim, ExpenseApprovalWorkflow
from authentication.models.user import User

class ExpenseCategorySerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'description', 'max_amount_per_claim',
            'requires_receipt', 'approval_required',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ExpenseClaimSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.name', read_only=True)
    employee_email = serializers.CharField(source='employee.user.email', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True)
    
    days_pending = serializers.SerializerMethodField()
    receipt_url = serializers.SerializerMethodField()
    
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = ExpenseClaim
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'category', 'category_name', 'title', 'description', 
            'amount', 'expense_date', 'receipt_image', 'receipt_url',
            'receipt_text', 'merchant_name', 'merchant_category',
            'status', 'submitted_at', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'approval_comments', 'reimbursement_amount',
            'paid_at', 'payment_reference', 'days_pending',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = [
            'id', 'receipt_text', 'submitted_at', 'reviewed_at',
            'paid_at', 'created_at', 'updated_at'
        ]

    def get_days_pending(self, obj):
        """Calculate days since submission"""
        if obj.submitted_at and obj.status not in ['Approved', 'Rejected', 'Paid']:
            from django.utils import timezone
            return (timezone.now() - obj.submitted_at).days
        return 0

    def get_receipt_url(self, obj):
        """Get full URL for receipt image"""
        if obj.receipt_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt_image.url)
            return obj.receipt_image.url
        return None

class ExpenseApprovalWorkflowSerializer(serializers.ModelSerializer):
    expense_title = serializers.CharField(source='expense_claim.title', read_only=True)
    expense_amount = serializers.DecimalField(source='expense_claim.amount', max_digits=12, decimal_places=2, read_only=True)
    employee_name = serializers.CharField(source='expense_claim.employee.user.name', read_only=True)
    approver_name = serializers.CharField(source='approver.name', read_only=True)
    
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    
    class Meta:
        model = ExpenseApprovalWorkflow
        fields = [
            'id', 'expense_claim', 'expense_title', 'expense_amount', 'employee_name',
            'approver', 'approver_name', 'level', 'status', 'comments', 'action_date',
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ExpenseStatsSerializer(serializers.Serializer):
    total_claims = serializers.IntegerField()
    total_amount_claimed = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount_approved = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount_paid = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_approvals = serializers.IntegerField()
    average_processing_days = serializers.DecimalField(max_digits=5, decimal_places=1)
