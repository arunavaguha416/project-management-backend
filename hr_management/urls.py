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
    path('employees/restore/', RestoreEmployee.as_view(), name='employee-restore'),
    path('employees/leave-requests/add/', LeaveRequestAdd.as_view(), name='leave-request-add'),
    path('employees/leave-requests/list/', LeaveRequestList.as_view(), name='leave-request-list'),
    path('employees/leave-requests/details/', LeaveRequestDetails.as_view(), name='leave-request-details'),
    path('employees/project/list/', EmployeeProjectList.as_view(), name='employee-project-list'),   
    path('employees/leave-requests/delete/<uuid:leave_request_id>/', LeaveRequestDelete.as_view(), name='leave-request-delete'),
    path('employees/leave-requests/restore/', RestoreLeaveRequest.as_view(), name='leave-request-restore'),
    path('employees/attendance/summary/', AttendanceSummary.as_view(), name='attendance-summary'),
    path('employees/birthdays/list/', BirthdayList.as_view(), name='birthday-summary'),    
    path('employees/leave-request/update/', LeaveRequestUpdate.as_view(), name='leave-update'),
    path('employee/attendance/list/', EmployeeAttendanceList.as_view(), name='employee-attendance-list'),
    path('employee/leave-requests/list/<uuid:id>/', EmployeeLeaveRequestList.as_view(), name='employee-leave-requestList'),

    path('manager/dashboard-metrics/', ManagerDashboardMetrics.as_view(), name='manager-dashboard-metrics'),
    path('manager/leave-requests/', ManagerLeaveRequests.as_view(), name='manager-leave-requests'),
    path('manager/leave-request/action/', ManagerLeaveAction.as_view(), name='manager-leave-action'),

    
    path('managers/available/', GetAvailableManagers.as_view(), name='get_available_managers'),
    path('projects/assignment-history/', ProjectAssignmentHistory.as_view(), name='project_assignment_history'),
    path('projects/bulk-assign/', BulkAssignProjects.as_view(), name='bulk_assign_projects'),
]