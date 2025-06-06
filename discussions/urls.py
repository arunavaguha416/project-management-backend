from django.urls import path
from .views.discussions_view import *

urlpatterns = [
    path('discussions/add/', DiscussionAdd.as_view(), name='discussion-add'),
    path('discussions/list/', DiscussionList.as_view(), name='discussion-list'),
    path('discussions/published/', PublishedDiscussionList.as_view(), name='discussion-published'),
    path('discussions/deleted/', DeletedDiscussionList.as_view(), name='discussion-deleted'),
    path('discussions/details/', DiscussionDetails.as_view(), name='discussion-details'),
    path('discussions/update/', DiscussionUpdate.as_view(), name='discussion-update'),
    path('discussions/publish/', ChangeDiscussionPublishStatus.as_view(), name='discussion-publish'),
    path('discussions/delete/<uuid:comment_id>/', DiscussionDelete.as_view(), name='discussion-delete'),
    path('discussions/restore/', RestoreDiscussion.as_view(), name='discussion-restore'),
]