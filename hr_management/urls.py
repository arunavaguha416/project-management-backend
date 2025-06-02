from django.urls import path
from . import views

urlpatterns = [
    path('employees/add/', views.EmployeeAdd.as_view(), name='employee-add'),
    path('employees/list/', views.EmployeeList.as_view(), name='employee-list'),
    path('employees/published/', views.PublishedEmployeeList.as_view(), name='employee-published'),
    path('employees/deleted/', views.DeletedEmployeeList.as_view(), name='employee-deleted'),
    path('employees/details/', views.EmployeeDetails.as_view(), name='employee-details'),
    path('employees/update/', views.EmployeeUpdate.as_view(), name='employee-update'),
    path('employees/publish/', views.ChangeEmployeePublishStatus.as_view(), name='employee-publish'),
    path('employees/delete/<uuid:employee_id>/', views.EmployeeDelete.as_view(), name='employee-delete'),
    path('employees/restore/', views.RestoreEmployee.as_view(), name='employee-restore'),
    path('leave-requests/add/', views.LeaveRequestAdd.as_view(), name='leave-request-add'),
    path('leave-requests/list/', views.LeaveRequestList.as_view(), name='leave-request-list'),
    path('leave-requests/published/', views.PublishedLeaveRequestList.as_view(), name='leave-request-published'),
    path('leave-requests/deleted/', views.DeletedLeaveRequestList.as_view(), name='leave-request-deleted'),
    path('leave-requests/details/', views.LeaveRequestDetails.as_view(), name='leave-request-details'),
    path('leave-requests/update/', views.LeaveRequestUpdate.as_view(), name='leave-request-update'),
    path('leave-requests/publish/', views.ChangeLeaveRequestPublishStatus.as_view(), name='leave-request-publish'),
    path('leave-requests/delete/<uuid:leave_request_id>/', views.LeaveRequestDelete.as_view(), name='leave-request-delete'),
    path('leave-requests/restore/', views.RestoreLeaveRequest.as_view(), name='leave-request-restore'),
]