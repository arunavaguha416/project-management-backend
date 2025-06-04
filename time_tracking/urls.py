from django.urls import path
from . import views

urlpatterns = [
    path('time-tracking/add/', views.TimeEntryAdd.as_view(), name='time-entry-add'),
    path('time-tracking/list/', views.TimeEntryList.as_view(), name='time-entry-list'),
    path('time-tracking/published/', views.PublishedTimeEntryList.as_view(), name='time-entry-published'),
    path('time-tracking/deleted/', views.DeletedTimeEntryList.as_view(), name='time-entry-deleted'),
    path('time-tracking/details/', views.TimeEntryDetails.as_view(), name='time-entry-details'),
    path('time-tracking/update/', views.TimeEntryUpdate.as_view(), name='time-entry-update'),
    path('time-tracking/publish/', views.ChangeTimeEntryPublishStatus.as_view(), name='time-entry-publish'),
    path('time-tracking/delete/<uuid:time_entry_id>/', views.TimeEntryDelete.as_view(), name='time-entry-delete'),
    path('time-tracking/restore/', views.RestoreTimeEntry.as_view(), name='time-entry-restore'),
]