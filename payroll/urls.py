from django.urls import path
from .views.payroll_views import *
from .views.expense_views import *
from .views.benefits_views import *
from .views.reports_views import *
from .views.payroll_validation import *
from .views.payroll_audit_views import *
from .views.payroll_rollback import *
from .views.payroll_period_views import *
from .views.salary_component import *
from .views.payroll_ai_views import *
from .views.loan_views import *

urlpatterns = [
    # Payroll periods
    path('periods/list/', PayrollPeriodList.as_view(), name='payroll-period-list'),
    path('periods/listing/', PayrollPeriodPaginatedList.as_view(), name='payroll-period-listing'),
    path('periods/add/', PayrollPeriodAdd.as_view(), name='payroll-period-add'),
    path('periods/update/', PayrollPeriodUpdateView.as_view(), name='payroll-period-update'),

    # Dashboard + details
    path('dashboard/summary/', PayrollDashboardSummary.as_view(), name='payroll-dashboard-summary'),
    path('dashboard/charts/', PayrollDashboardCharts.as_view(), name='payroll-dashboard-charts'),
    path('details/', PayrollDetailView.as_view(), name='payroll-details'),

    # Payslip + form16
    path('payslip/download/', PayslipDownloadView.as_view(), name='payroll-payslip-download'),
    path('payslip/generate/', PayslipGenerateView.as_view(), name='payroll-payslip-generate'),
    path('employee/payslips/', EmployeePayslipListView.as_view(), name='payroll-employee-payslips'),
    path('form16/summary/', Form16SummaryView.as_view(), name='payroll-form16-summary'),
    path('form16/download/', Form16DownloadView.as_view(), name='payroll-form16-download'),

    # Pay runs
    path('pay-runs/list/', PayRunListView.as_view(), name='payrun-list'),
    path('pay-runs/create/', PayRunCreateView.as_view(), name='payrun-create'),
    path('pay-runs/generate/', PayRunGeneratePayrollView.as_view(), name='payrun-generate'),
    path('pay-runs/employees/', PayRunEmployeeListView.as_view(), name='payrun-employees'),
    path('pay-runs/finalize/', PayRunFinalizeView.as_view(), name='payrun-finalize'),
    path('pay-runs/summary/', PayRunSummaryView.as_view(), name='payrun-summary'),
    path('pay-runs/lock-status/', PayRunLockCheckView.as_view(), name='payrun-lock-status'),
    path('pay-runs/reconciliation/', PayRunReconciliationView.as_view(), name='payrun-reconciliation'),
    path('pay-runs/variance/', PayRunVarianceView.as_view(), name='payrun-variance'),
    path('pay-runs/validate/', PayrollValidationView.as_view(), name='payrun-validate'),
    path('pay-runs/rollback/', PayrollRollbackView.as_view(), name='payrun-rollback'),
    path('approve-all/', PayRunApproveAllView.as_view(), name='payrun-approve-all'),
    path('approve/', PayrollApprove.as_view(), name='payroll-approve-single'),

    # Payroll AI
    path('ai/chat/', PayrollAIChatView.as_view(), name='payroll-ai-chat'),

    # Reports
    path('reports/dashboard/', StatutoryDashboardView.as_view(), name='reports-dashboard'),
    path('reports/pf/', PFReportView.as_view(), name='reports-pf'),
    path('reports/pt/', PTReportView.as_view(), name='reports-pt'),
    path('reports/tds/', TDSReportView.as_view(), name='reports-tds'),
    path('reports/pf/excel/', PFExcelExportView.as_view(), name='reports-pf-excel'),
    path('reports/pt/excel/', PTExcelExportView.as_view(), name='reports-pt-excel'),
    path('reports/tds/excel/', TDSExcelExportView.as_view(), name='reports-tds-excel'),
    path('reports/pf/export/', PFExcelExportView.as_view(), name='reports-pf-export'),
    path('reports/pt/export/', PTExcelExportView.as_view(), name='reports-pt-export'),
    path('reports/tds/export/', TDSExcelExportView.as_view(), name='reports-tds-export'),
    path('reports/challans/', StatutoryChallanListView.as_view(), name='reports-challans'),
    path('reports/challan/mark-paid/', StatutoryChallanMarkPaidView.as_view(), name='reports-challan-mark-paid'),
    path('reports/bank-disbursement/export/', BankDisbursementExportView.as_view(), name='bank-disbursement-export'),
    path('challans/list/', StatutoryChallanListView.as_view(), name='challans-list'),
    path('challans/mark-paid/', StatutoryChallanMarkPaidView.as_view(), name='challans-mark-paid'),

    # Audit trail
    path('audit-trail/', PayrollAuditTrailView.as_view(), name='payroll-audit-trail'),

    # Salary components
    path('salary-components/list/', SalaryComponentListView.as_view(), name='salary-components-list'),
    path('salary-components/create/', SalaryComponentCreateView.as_view(), name='salary-components-create'),
    path('salary-components/update/', SalaryComponentUpdateView.as_view(), name='salary-components-update'),
    path('salary-components/toggle/', SalaryComponentToggleView.as_view(), name='salary-components-toggle'),

    # Benefits
    path('benefits/list/', BenefitPlanList.as_view(), name='benefits-list'),
    path('benefits/add/', BenefitPlanAdd.as_view(), name='benefits-add'),
    path('benefits/update/', BenefitPlanUpdate.as_view(), name='benefits-update'),
    path('benefits/delete/', BenefitPlanDelete.as_view(), name='benefits-delete'),
    path('benefits/enrollments/list/', BenefitEnrollmentList.as_view(), name='benefit-enrollments-list'),
    path('benefits/enrollments/add/', BenefitEnrollmentAdd.as_view(), name='benefit-enrollments-add'),
    path('benefits/enrollments/update/', BenefitEnrollmentUpdate.as_view(), name='benefit-enrollments-update'),
    path('benefits/enrollments/approve/', BenefitEnrollmentApprove.as_view(), name='benefit-enrollments-approve'),
    path('benefits/enrollments/cancel/', BenefitEnrollmentCancel.as_view(), name='benefit-enrollments-cancel'),
    path('benefits/enrollments/delete/', BenefitEnrollmentDelete.as_view(), name='benefit-enrollments-delete'),
    path('benefits/stats/', BenefitsStats.as_view(), name='benefits-stats'),
    path('benefits/export/', BenefitsExport.as_view(), name='benefits-export'),

    # Expenses
    path('expenses/list/', ExpenseClaimList.as_view(), name='expenses-list'),
    path('expenses/add/', ExpenseClaimAdd.as_view(), name='expenses-add'),
    path('expenses/update/', ExpenseClaimUpdate.as_view(), name='expenses-update'),
    path('expenses/submit/', ExpenseClaimSubmit.as_view(), name='expenses-submit'),
    path('expenses/approve/', ExpenseClaimApprove.as_view(), name='expenses-approve'),
    path('expenses/delete/', ExpenseClaimDelete.as_view(), name='expenses-delete'),
    path('expenses/stats/', ExpenseStats.as_view(), name='expenses-stats'),
    path('expenses/export/', ExpenseExport.as_view(), name='expenses-export'),
    path('expenses/categories/list/', ExpenseCategoryList.as_view(), name='expense-categories-list'),
    path('expenses/categories/add/', ExpenseCategoryAdd.as_view(), name='expense-categories-add'),
    path('expenses/categories/update/', ExpenseCategoryUpdate.as_view(), name='expense-categories-update'),
    path('expenses/categories/delete/', ExpenseCategoryDelete.as_view(), name='expense-categories-delete'),

    # Loans & Advances
    path('loans/list/', LoanAdvanceList.as_view(), name='loans-list'),
    path('loans/add/', LoanAdvanceAdd.as_view(), name='loans-add'),
    path('loans/update/', LoanAdvanceUpdate.as_view(), name='loans-update'),
    path('loans/stats/', LoanAdvanceStats.as_view(), name='loans-stats'),
    path('loans/schedule/', LoanAdvanceSchedule.as_view(), name='loans-schedule'),
    path('loans/employee-options/', LoanAdvanceEmployeeOptions.as_view(), name='loans-employee-options'),
]
