# payroll/urls.py

from django.urls import path
from .views.payroll_views import *
from .views.expense_views import *
from .views.benefits_views import *

urlpatterns = [
    # ===============================
    # PAYROLL PERIODS MANAGEMENT
    # ===============================
    path('periods/list/', PayrollPeriodList.as_view(), name='payroll-period-list'),
    path('periods/add/', PayrollPeriodAdd.as_view(), name='payroll-period-add'),
    path('dashboard/summary/', PayrollDashboardSummary.as_view(), name='payroll-dashboard-summary'),
    path('dashboard/charts/', PayrollDashboardCharts.as_view(), name='payroll-dashboard-charts'),

    # ===============================
    # PAYROLL GENERATION & MANAGEMENT
    # ===============================
    path('generate/', PayrollGenerate.as_view(), name='payroll-generate'),
    path('list/', PayrollList.as_view(), name='payroll-list'),
    path('approve/', PayrollApprove.as_view(), name='payroll-approve'),
    
    # ===============================
    # PAYROLL ANALYTICS & REPORTS
    # ===============================
    path('stats/', PayrollStats.as_view(), name='payroll-stats'),
    
    # ===============================
    # PERFORMANCE METRICS
    # ===============================
    path('performance-metrics/list/', PerformanceMetricList.as_view(), name='performance-metric-list'),
    path('performance-metrics/add/', PerformanceMetricAdd.as_view(), name='performance-metric-add'),
    
    # ===============================
    # EXPENSE MANAGEMENT
    # ===============================
    # Expense Categories
    path('expenses/categories/list/', ExpenseCategoryList.as_view(), name='expense-category-list'),
    path('expenses/categories/add/', ExpenseCategoryAdd.as_view(), name='expense-category-add'),
    path('expenses/categories/update/', ExpenseCategoryUpdate.as_view(), name='expense-category-update'),
    path('expenses/categories/delete/', ExpenseCategoryDelete.as_view(), name='expense-category-delete'),
    
    # Expense Claims
    path('expenses/claims/list/', ExpenseClaimList.as_view(), name='expense-claim-list'),
    path('expenses/claims/add/', ExpenseClaimAdd.as_view(), name='expense-claim-add'),
    path('expenses/claims/update/', ExpenseClaimUpdate.as_view(), name='expense-claim-update'),
    path('expenses/claims/submit/', ExpenseClaimSubmit.as_view(), name='expense-claim-submit'),
    path('expenses/claims/approve/', ExpenseClaimApprove.as_view(), name='expense-claim-approve'),
    path('expenses/claims/delete/', ExpenseClaimDelete.as_view(), name='expense-claim-delete'),
    
    # Expense Receipt Processing
    path('expenses/receipt/upload/', ReceiptUpload.as_view(), name='receipt-upload'),
    path('expenses/receipt/process/', ReceiptProcess.as_view(), name='receipt-process'),
    
    # Expense Reports
    path('expenses/stats/', ExpenseStats.as_view(), name='expense-stats'),
    path('expenses/export/', ExpenseExport.as_view(), name='expense-export'),
    
    # ===============================
    # BENEFITS MANAGEMENT
    # ===============================
    # Benefit Plans
    path('benefits/plans/list/', BenefitPlanList.as_view(), name='benefit-plan-list'),
    path('benefits/plans/add/', BenefitPlanAdd.as_view(), name='benefit-plan-add'),
    path('benefits/plans/details/', BenefitPlanDetails.as_view(), name='benefit-plan-details'),
    path('benefits/plans/update/', BenefitPlanUpdate.as_view(), name='benefit-plan-update'),
    path('benefits/plans/delete/', BenefitPlanDelete.as_view(), name='benefit-plan-delete'),
    
    # Benefit Enrollments
    path('benefits/enrollments/list/', BenefitEnrollmentList.as_view(), name='benefit-enrollment-list'),
    path('benefits/enrollments/add/', BenefitEnrollmentAdd.as_view(), name='benefit-enrollment-add'),
    path('benefits/enrollments/update/', BenefitEnrollmentUpdate.as_view(), name='benefit-enrollment-update'),
    path('benefits/enrollments/approve/', BenefitEnrollmentApprove.as_view(), name='benefit-enrollment-approve'),
    path('benefits/enrollments/cancel/', BenefitEnrollmentCancel.as_view(), name='benefit-enrollment-cancel'),
    path('benefits/enrollments/delete/', BenefitEnrollmentDelete.as_view(), name='benefit-enrollment-delete'),
    
    # Benefits Reports
    path('benefits/stats/', BenefitsStats.as_view(), name='benefits-stats'),
    path('benefits/export/', BenefitsExport.as_view(), name='benefits-export'),
    
    # ===============================
    # TAX CONFIGURATION
    # ===============================
    path('tax-config/list/', TaxConfigurationList.as_view(), name='tax-configuration-list'),
    path('tax-config/add/', TaxConfigurationAdd.as_view(), name='tax-configuration-add'),
    path('tax-config/update/', TaxConfigurationUpdate.as_view(), name='tax-configuration-update'),
    path('tax-config/activate/', TaxConfigurationActivate.as_view(), name='tax-configuration-activate'),
    path('tax-config/delete/', TaxConfigurationDelete.as_view(), name='tax-configuration-delete'),
    
    # Tax Calculations
    path('tax-calculator/', TaxCalculator.as_view(), name='tax-calculator'),
]
