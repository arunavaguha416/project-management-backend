# payroll/urls.py

from django.urls import path
from .views.payroll_views import *
from .views.expense_views import *
from .views.benefits_views import *
from .views.reports_views import *

urlpatterns = [
    # ===============================
    # PAYROLL PERIODS MANAGEMENT
    # ===============================
    path('periods/list/', PayrollPeriodList.as_view(), name='payroll-period-list'),
    path('periods/add/', PayrollPeriodAdd.as_view(), name='payroll-period-add'),
    path('dashboard/summary/', PayrollDashboardSummary.as_view(), name='payroll-dashboard-summary'),
    path('dashboard/charts/', PayrollDashboardCharts.as_view(), name='payroll-dashboard-charts'),
    path('details/', PayrollDetailView.as_view(), name='payroll-dashboard-charts'),
    path('payslip/download/', PayslipDownloadView.as_view()),
    path('payslip/generate/', PayslipGenerateView.as_view()),
    path('employee/payslips/', EmployeePayslipListView.as_view()),
    path('form16/summary/', Form16SummaryView.as_view()),
    path('form16/download/', Form16DownloadView.as_view()),


    

    # Pay Runs
    path('pay-runs/list/', PayRunListView.as_view()),
    path('pay-runs/create/', PayRunCreateView.as_view()),
    path('pay-runs/generate/', PayRunGeneratePayrollView.as_view()),
    path('pay-runs/employees/', PayRunEmployeeListView.as_view()),
    path('pay-runs/finalize/', PayRunFinalizeView.as_view()),
    path('pay-runs/summary/', PayRunSummaryView.as_view()),
    path('pay-runs/lock-status/', PayRunLockCheckView.as_view()),


    # payroll/urls.py
    path("reports/pf/", PFReportView.as_view()),
    path("reports/pt/", PTReportView.as_view()),
    path("reports/tds/", TDSReportView.as_view()),

    
    path("reports/pf/excel/", PFExcelExportView.as_view()),
    path("reports/pt/excel/", PTExcelExportView.as_view()),
    path("reports/tds/excel/", TDSExcelExportView.as_view()),
    path("reports/dashboard/", StatutoryDashboardView.as_view()),
    path("reports/challans/", StatutoryChallanListView.as_view()),
    path("reports/challan/mark-paid/", StatutoryChallanMarkPaidView.as_view()),

    path("reports/pf/export/", PFExcelExportView.as_view()),
    path("reports/pt/export/", PTExcelExportView.as_view()),
    path("reports/tds/export/", TDSExcelExportView.as_view()),
    # payroll/urls.py
    path("reports/bank-disbursement/export/", BankDisbursementExportView.as_view(),name="bank-disbursement-export"),
    

    path('challans/list/', StatutoryChallanListView.as_view()),
    path('challans/mark-paid/', StatutoryChallanMarkPaidView.as_view()),


    

]
