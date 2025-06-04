from django.urls import path
from . import views

urlpatterns = [
    path('attachments/add/', views.AttachmentAdd.as_view(), name='attachment-add'),
    path('attachments/list/', views.AttachmentList.as_view(), name='attachment-list'),
    path('attachments/published/', views.PublishedAttachmentList.as_view(), name='attachment-published'),
    path('attachments/deleted/', views.DeletedAttachmentList.as_view(), name='attachment-deleted'),
    path('attachments/details/', views.AttachmentDetails.as_view(), name='attachment-details'),
    path('attachments/update/', views.AttachmentUpdate.as_view(), name='attachment-update'),
    path('attachments/publish/', views.ChangeAttachmentPublishStatus.as_view(), name='attachment-publish'),
    path('attachments/delete/<uuid:attachment_id>/', views.AttachmentDelete.as_view(), name='attachment-delete'),
    path('attachments/restore/', views.RestoreAttachment.as_view(), name='attachment-restore'),
]