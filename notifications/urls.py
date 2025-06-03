from django.urls import path
from . import views

urlpatterns = [
    path('notifications/add/', views.NotificationAdd.as_view(), name='notification-add'),
    path('notifications/list/', views.NotificationList.as_view(), name='notification-list'),
    path('notifications/published/', views.PublishedNotificationList.as_view(), name='notification-published'),
    path('notifications/deleted/', views.DeletedNotificationList.as_view(), name='notification-deleted'),
    path('notifications/details/', views.NotificationDetails.as_view(), name='notification-details'),
    path('notifications/update/', views.NotificationUpdate.as_view(), name='notification-update'),
    path('notifications/publish/', views.ChangeNotificationPublishStatus.as_view(), name='notification-publish'),
    path('notifications/delete/<int:notification_id>/', views.NotificationDelete.as_view(), name='notification-delete'),
    path('notifications/restore/', views.RestoreNotification.as_view(), name='notification-restore'),
    path('notifications/mark-read/', views.MarkNotificationRead.as_view(), name='notification-mark-read'),
]