# department/urls.py
from django.urls import path
from .views.depertment_view import *

# URL patterns for department-related API endpoints
urlpatterns = [
    path('add/', DepartmentAdd.as_view(), name='department-add'),
    path('list/', DepartmentList.as_view(), name='department-list'),
    path('published/', PublishedDepartmentList.as_view(), name='department-published-list'),
    path('deleted/', DepartmentList.as_view(), name='department-deleted-list'),
    path('details/', DepartmentDetails.as_view(), name='department-details'),
    path('update/', DepartmentUpdate.as_view(), name='department-update'),
    path('publish/', ChangeDepartmentPublishStatus.as_view(), name='department-publish-status'),
    path('delete/<uuid:department_id>/', DepartmentDelete.as_view(), name='department-delete'),
    path('restore/', RestoreDepartment.as_view(), name='department-restore'),
]