from django.urls import path
from .views.team_views import *

urlpatterns = [
    path('add/', TeamAdd.as_view(), name='team-add'),
    path('list/', TeamList.as_view(), name='team-list'),
    path('deleted/', DeletedTeamList.as_view(), name='team-deleted'),
    path('details/', TeamDetails.as_view(), name='team-details'),
    path('update/', TeamUpdate.as_view(), name='team-update'),
    path('delete/<uuid:time_entry_id>/', TeamDelete.as_view(), name='team-delete'),
    path('restore/', RestoreTeam.as_view(), name='team-restore'),
    path('project/members/', ProjectTeamMembers.as_view(), name='project-team-member'),
    path('members/', ManagerTeamMembers.as_view(), name='team-member'),
]