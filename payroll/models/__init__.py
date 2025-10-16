# payroll/models/__init__.py

# Import all payroll-related models
from .payroll_models import (
    PayrollPeriod,
    Payroll,
    PerformanceMetric
)

# Import all expense-related models
from .expense_models import (
    ExpenseCategory,
    ExpenseClaim,
    ExpenseApprovalWorkflow
)

# Import all benefits-related models
from .benefits_models import (
    BenefitPlan,
    BenefitEnrollment,
    TaxConfiguration
)

# Make all models available when importing from models package
__all__ = [
    # Payroll Models
    'PayrollPeriod',
    'Payroll', 
    'PerformanceMetric',
    
    # Expense Models
    'ExpenseCategory',
    'ExpenseClaim',
    'ExpenseApprovalWorkflow',
    
    # Benefits Models
    'BenefitPlan',
    'BenefitEnrollment',
    'TaxConfiguration',
]
