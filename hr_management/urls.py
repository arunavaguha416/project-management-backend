from django.urls import path
from .views.hr_management_views import *

urlpatterns = [
    path('employees/add/', EmployeeAdd.as_view(), name='employee-add'),
    path('employees/list/', EmployeeList.as_view(), name='employee-list'),
    path('employees/published/', PublishedEmployeeList.as_view(), name='employee-published'),
    path('employees/deleted/', DeletedEmployeeList.as_view(), name='employee-deleted'),
    path('employees/details/', EmployeeDetails.as_view(), name='employee-details'),
    path('employees/update/', EmployeeUpdate.as_view(), name='employee-update'),
    path('employees/publish/', ChangeEmployeePublishStatus.as_view(), name='employee-publish'),
    path('employees/delete/<uuid:employee_id>/', EmployeeDelete.as_view(), name='employee-delete'),
    path('employees/restore/', RestoreEmployee.as_view(), name='employee-restore'),
    path('leave-requests/add/', LeaveRequestAdd.as_view(), name='leave-request-add'),
    path('leave-requests/list/', LeaveRequestList.as_view(), name='leave-request-list'),
    path('leave-requests/published/', PublishedLeaveRequestList.as_view(), name='leave-request-published'),
    path('leave-requests/deleted/', DeletedLeaveRequestList.as_view(), name='leave-request-deleted'),
    path('leave-requests/details/', LeaveRequestDetails.as_view(), name='leave-request-details'),
    path('leave-requests/update/', LeaveRequestUpdate.as_view(), name='leave-request-update'),
    path('leave-requests/publish/', ChangeLeaveRequestPublishStatus.as_view(), name='leave-request-publish'),
    path('leave-requests/delete/<uuid:leave_request_id>/', LeaveRequestDelete.as_view(), name='leave-request-delete'),
    path('leave-requests/restore/', RestoreLeaveRequest.as_view(), name='leave-request-restore'),
]