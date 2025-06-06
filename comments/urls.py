from django.urls import path
from .views.comment_view import *

urlpatterns = [
    path('comments/add/', CommentAdd.as_view(), name='comment-add'),
    path('comments/list/', CommentList.as_view(), name='comment-list'),
    path('comments/published/', PublishedCommentList.as_view(), name='comment-published'),
    path('comments/deleted/', DeletedCommentList.as_view(), name='comment-deleted'),
    path('comments/details/', CommentDetails.as_view(), name='comment-details'),
    path('comments/update/', CommentUpdate.as_view(), name='comment-update'),
    path('comments/publish/', ChangeCommentPublishStatus.as_view(), name='comment-publish'),
    path('comments/delete/<uuid:comment_id>/', CommentDelete.as_view(), name='comment-delete'),
    path('comments/restore/', RestoreComment.as_view(), name='comment-restore'),
]