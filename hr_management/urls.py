from django.urls import path
from .views.hr_management_views import *

urlpatterns = [
    path('employees/add/', EmployeeAdd.as_view(), name='employee-add'),
    path('employees/list/', EmployeeList.as_view(), name='employee-list'),
    path('manager/list/', ManagerList.as_view(), name='employee-list'),
    path('employees/deleted/', DeletedEmployeeList.as_view(), name='employee-deleted'),
    path('employees/details/', EmployeeDetails.as_view(), name='employee-details'),
    path('employees/update/', EmployeeUpdate.as_view(), name='employee-update'),
    path('employees/delete/<uuid:employee_id>/', EmployeeDelete.as_view(), name='employee-delete'),    
    path('employees/project/list/', EmployeeProjectList.as_view(), name='employee-project-list'),   
    path('employees/attendance/summary/', AttendanceSummary.as_view(), name='attendance-summary'),
    path('employees/birthdays/list/', BirthdayList.as_view(), name='birthday-summary'),    
    path('employee/attendance/list/', EmployeeAttendanceList.as_view(), name='employee-attendance-list'),
    path('manager/dashboard-metrics/', ManagerDashboardMetrics.as_view(), name='manager-dashboard-metrics'),    
    path('managers/available/', GetAvailableManagers.as_view(), name='get_available_managers'),
    path('projects/assignment-history/', ProjectAssignmentHistory.as_view(), name='project_assignment_history'),
    path('projects/bulk-assign/', BulkAssignProjects.as_view(), name='bulk_assign_projects'),

    # ==================== NEW STREAMLINED LEAVE MANAGEMENT ROUTES ====================
    # Function 1: List leave requests (HR & MANAGER)
    path('leave-requests/list/', LeaveRequestsList.as_view(), name='leave-requests-list'),
    
    # Function 2: Apply leave (HR, MANAGER, EMPLOYEE)
    path('leave/apply/', ApplyLeave.as_view(), name='apply-leave'),
    
    # Function 3: Approve/Reject leave (HR & MANAGER)
    path('leave/approve-reject/', ApproveRejectLeave.as_view(), name='approve-reject-leave'),
    
    # Function 4: Current user leave balance
    path('leave/my-balance/', CurrentUserLeaveBalance.as_view(), name='my-leave-balance'),
    
    # Function 5: Employee leave balance (for HR/MANAGER)
    path('leave/employee-balance/', EmployeeLeaveBalance.as_view(), name='employee-leave-balance'),

    # Add this line to urlpatterns in urls.py
    path('hr/dashboard-metrics/', HRDashboardMetrics.as_view(), name='hr-dashboard-metrics'),
]
