from django.urls import path
from .views.attachment_view import *

urlpatterns = [
    path('attachments/add/', AttachmentAdd.as_view(), name='attachment-add'),
    path('attachments/list/', AttachmentList.as_view(), name='attachment-list'),
    path('attachments/published/', PublishedAttachmentList.as_view(), name='attachment-published'),
    path('attachments/deleted/', DeletedAttachmentList.as_view(), name='attachment-deleted'),
    path('attachments/details/', AttachmentDetails.as_view(), name='attachment-details'),
    path('attachments/update/', AttachmentUpdate.as_view(), name='attachment-update'),
    path('attachments/publish/', ChangeAttachmentPublishStatus.as_view(), name='attachment-publish'),
    path('attachments/delete/<uuid:attachment_id>/', AttachmentDelete.as_view(), name='attachment-delete'),
    path('attachments/restore/', RestoreAttachment.as_view(), name='attachment-restore'),
]