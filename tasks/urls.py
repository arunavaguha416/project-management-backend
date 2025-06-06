from django.urls import path
from .views.views import *

urlpatterns = [
    path('tasks/add/', TaskAdd.as_view(), name='task-add'),
    path('tasks/list/', TaskList.as_view(), name='task-list'),
    path('tasks/published/', PublishedTaskList.as_view(), name='task-published'),
    path('tasks/deleted/', DeletedTaskList.as_view(), name='task-deleted'),
    path('tasks/details/', TaskDetails.as_view(), name='task-details'),
    path('tasks/update/', TaskUpdate.as_view(), name='task-update'),
    path('tasks/publish/', ChangeTaskPublishStatus.as_view(), name='task-publish'),
    path('tasks/delete/<uuid:task_id>/', TaskDelete.as_view(), name='task-delete'),
    path('tasks/restore/', RestoreTask.as_view(), name='task-restore'),
]