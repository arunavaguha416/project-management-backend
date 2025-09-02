from django.urls import path
from .views.time_tracking_views import *

urlpatterns = [
    # Time tracking endpoints
    path('login-time/', RecordLoginTime.as_view(), name='record-login-time'),
    path('logout-time/', RecordLogoutTime.as_view(), name='record-logout-time'),
    path('entries/list/', TimeEntryList.as_view(), name='time-entries-list'),
    path('entries/stats/', UserTimeStats.as_view(), name='user-time-stats'),
    path('entries/add/', ManualTimeEntry.as_view(), name='manual-time-entry'),
    path('entries/update/', TimeEntryUpdate.as_view(), name='time-entry-update'),
    path('entries/delete/<uuid:entry_id>/', TimeEntryDelete.as_view(), name='time-entry-delete'),
]
