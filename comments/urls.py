from django.urls import path
from . import views

urlpatterns = [
    path('comments/add/', views.CommentAdd.as_view(), name='comment-add'),
    path('comments/list/', views.CommentList.as_view(), name='comment-list'),
    path('comments/published/', views.PublishedCommentList.as_view(), name='comment-published'),
    path('comments/deleted/', views.DeletedCommentList.as_view(), name='comment-deleted'),
    path('comments/details/', views.CommentDetails.as_view(), name='comment-details'),
    path('comments/update/', views.CommentUpdate.as_view(), name='comment-update'),
    path('comments/publish/', views.ChangeCommentPublishStatus.as_view(), name='comment-publish'),
    path('comments/delete/<uuid:comment_id>/', views.CommentDelete.as_view(), name='comment-delete'),
    path('comments/restore/', views.RestoreComment.as_view(), name='comment-restore'),
]