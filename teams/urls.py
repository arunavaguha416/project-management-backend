from django.urls import path
from .views.team_views import *

urlpatterns = [
    path('team/add/', TeamAdd.as_view(), name='team-add'),
    path('team/list/', TeamList.as_view(), name='team-list'),
    path('team/published/', PublishedTeamList.as_view(), name='team-published'),
    path('team/deleted/', DeletedTeamList.as_view(), name='team-deleted'),
    path('team/details/', TeamDetails.as_view(), name='team-details'),
    path('team/update/', TeamUpdate.as_view(), name='team-update'),
    path('team/publish/', ChangeTeamPublishStatus.as_view(), name='team-publish'),
    path('team/delete/<uuid:time_entry_id>/', TeamDelete.as_view(), name='team-delete'),
    path('team/restore/', RestoreTeam.as_view(), name='team-restore'),
]