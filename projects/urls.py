from django.urls import path
from .views.projects_views import *
from .views.task_views import *
from .views.comment_view import *
from .views.sprint_views import *


urlpatterns = [
     path('project/add/', ProjectAdd.as_view(), name='project_add'),
    path('project/list/', ProjectList.as_view(), name='project_list'),
    path('project/published/', PublishedProjectList.as_view(), name='published_project_list'),
    path('project/deleted/', DeletedProjectList.as_view(), name='deleted_project_list'),
    path('project/details/', ProjectDetails.as_view(), name='project_details'),
    path('project/update/', ProjectUpdate.as_view(), name='project_update'),
    path('project/publish/', ChangeProjectPublishStatus.as_view(), name='project_publish'),
    path('project/delete/<uuid:project_id>/', ProjectDelete.as_view(), name='project_delete'),
    path('project/restore/', RestoreProject.as_view(), name='project_restore'),

    path('sprint/add/', SprintAdd.as_view(), name='sprint_add'),
    path('sprint/list/', SprintList.as_view(), name='sprint_list'),
    path('sprint/details/', SprintDetails.as_view(), name='sprint_details'),
    path('sprint/update/', SprintUpdate.as_view(), name='sprint_update'),
    path('sprint/delete/<uuid:sprint_id>/', SprintDelete.as_view(), name='sprint_delete'),
    path('sprint/restore/', RestoreSprint.as_view(), name='sprint_restore'),
    path('sprint/add-project/', AddProjectToSprint.as_view(), name='add_project_to_sprint'),
    path('sprint/remove-project/', RemoveProjectFromSprint.as_view(), name='remove_project_from_sprint'),

    path('task/add/', TaskAdd.as_view(), name='task_add'),
    path('task/list/', SprintTaskList.as_view(), name='sprint_task_list'),
    path('task/details/', TaskDetails.as_view(), name='task_details'),
    path('task/update/', TaskUpdate.as_view(), name='task_update'),
    path('task/move/', TaskMove.as_view(), name='task_move'),
    path('task/delete/<uuid:task_id>/', TaskDelete.as_view(), name='task_delete'),
    path('task/restore/', RestoreTask.as_view(), name='task_restore'),

    path('comments/add/', CommentAdd.as_view(), name='comment-add'),
    path('comments/list/', CommentList.as_view(), name='comment-list'),
    path('comments/details/', CommentDetails.as_view(), name='comment-details'),
    path('comments/update/', CommentUpdate.as_view(), name='comment-update'),
    path('comments/delete/<uuid:comment_id>/', CommentDelete.as_view(), name='comment-delete'),
    path('comments/restore/', RestoreComment.as_view(), name='comment-restore'),
]