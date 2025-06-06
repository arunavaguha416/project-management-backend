from django.urls import path
from .views.time_tracking_views import *

urlpatterns = [
    path('time-tracking/add/', TimeEntryAdd.as_view(), name='time-entry-add'),
    path('time-tracking/list/', TimeEntryList.as_view(), name='time-entry-list'),
    path('time-tracking/published/', PublishedTimeEntryList.as_view(), name='time-entry-published'),
    path('time-tracking/deleted/', DeletedTimeEntryList.as_view(), name='time-entry-deleted'),
    path('time-tracking/details/', TimeEntryDetails.as_view(), name='time-entry-details'),
    path('time-tracking/update/', TimeEntryUpdate.as_view(), name='time-entry-update'),
    path('time-tracking/publish/', ChangeTimeEntryPublishStatus.as_view(), name='time-entry-publish'),
    path('time-tracking/delete/<uuid:time_entry_id>/', TimeEntryDelete.as_view(), name='time-entry-delete'),
    path('time-tracking/restore/', RestoreTimeEntry.as_view(), name='time-entry-restore'),
]