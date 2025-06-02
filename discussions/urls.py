from django.urls import path
from . import views

urlpatterns = [
    path('discussions/add/', views.CommentAdd.as_view(), name='comment-add'),
    path('discussions/list/', views.CommentList.as_view(), name='comment-list'),
    path('discussions/published/', views.PublishedCommentList.as_view(), name='comment-published'),
    path('discussions/deleted/', views.DeletedCommentList.as_view(), name='comment-deleted'),
    path('discussions/details/', views.CommentDetails.as_view(), name='comment-details'),
    path('discussions/update/', views.CommentUpdate.as_view(), name='comment-update'),
    path('discussions/publish/', views.ChangeCommentPublishStatus.as_view(), name='comment-publish'),
    path('discussions/delete/<uuid:comment_id>/', views.CommentDelete.as_view(), name='comment-delete'),
    path('discussions/restore/', views.RestoreComment.as_view(), name='comment-restore'),
]