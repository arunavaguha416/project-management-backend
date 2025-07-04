from django.urls import path
from .views.projects_views import *
from .views.task_views import *
from .views.comment_view import *


urlpatterns = [
    path('add/', ProjectAdd.as_view(), name='project-add'),
    path('list/', ProjectList.as_view(), name='project-list'),
    path('published/', PublishedProjectList.as_view(), name='project-published'),
    path('deleted/', DeletedProjectList.as_view(), name='project-deleted'),
    path('details/', ProjectDetails.as_view(), name='project-details'),
    path('update/', ProjectUpdate.as_view(), name='project-update'),
    path('publish/', ChangeProjectPublishStatus.as_view(), name='project-publish'),
    path('delete/<uuid:project_id>/', ProjectDelete.as_view(), name='project-delete'),
    path('restore/', RestoreProject.as_view(), name='project-restore'),

    path('tasks/add/', TaskAdd.as_view(), name='task-add'),
    path('tasks/list/', TaskList.as_view(), name='task-list'),
    path('tasks/published/', PublishedTaskList.as_view(), name='task-published'),
    path('tasks/deleted/', DeletedTaskList.as_view(), name='task-deleted'),
    path('tasks/details/', TaskDetails.as_view(), name='task-details'),
    path('tasks/update/', TaskUpdate.as_view(), name='task-update'),
    path('tasks/publish/', ChangeTaskPublishStatus.as_view(), name='task-publish'),
    path('tasks/delete/<uuid:task_id>/', TaskDelete.as_view(), name='task-delete'),
    path('tasks/restore/', RestoreTask.as_view(), name='task-restore'),

    path('comments/add/', CommentAdd.as_view(), name='comment-add'),
    path('comments/list/', CommentList.as_view(), name='comment-list'),
    path('comments/published/', PublishedCommentList.as_view(), name='comment-published'),
    path('comments/deleted/', DeletedCommentList.as_view(), name='comment-deleted'),
    path('comments/details/', CommentDetails.as_view(), name='comment-details'),
    path('comments/update/', CommentUpdate.as_view(), name='comment-update'),
    path('comments/delete/<uuid:comment_id>/', CommentDelete.as_view(), name='comment-delete'),
    path('comments/restore/', RestoreComment.as_view(), name='comment-restore'),
]