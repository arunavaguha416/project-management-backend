# department/urls.py
from django.urls import path
from .views.department_view import *

# URL patterns for department-related API endpoints
urlpatterns = [
    path('add/', DepartmentAdd.as_view(), name='department-add'),
    path('list/', DepartmentList.as_view(), name='department-list'),
    path('deleted/', DepartmentList.as_view(), name='department-deleted-list'),
    path('details/', DepartmentDetails.as_view(), name='department-details'),
    path('update/', DepartmentUpdate.as_view(), name='department-update'),
    path('delete/<uuid:department_id>/', DepartmentDelete.as_view(), name='department-delete'),
    path('restore/', RestoreDepartment.as_view(), name='department-restore'),
]