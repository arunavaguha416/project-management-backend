from django.urls import path
from .views.notification_view import *

urlpatterns = [
    path('notifications/add/', NotificationAdd.as_view(), name='notification-add'),
    path('notifications/list/', NotificationList.as_view(), name='notification-list'),
    path('notifications/published/', PublishedNotificationList.as_view(), name='notification-published'),
    path('notifications/deleted/', DeletedNotificationList.as_view(), name='notification-deleted'),
    path('notifications/details/', NotificationDetails.as_view(), name='notification-details'),
    path('notifications/update/', NotificationUpdate.as_view(), name='notification-update'),
    path('notifications/publish/', ChangeNotificationPublishStatus.as_view(), name='notification-publish'),
    path('notifications/delete/<int:notification_id>/', NotificationDelete.as_view(), name='notification-delete'),
    path('notifications/restore/', RestoreNotification.as_view(), name='notification-restore'),
    path('notifications/mark-read/', MarkNotificationRead.as_view(), name='notification-mark-read'),
]