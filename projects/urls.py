from django.urls import path
from .views.views import *

urlpatterns = [
    path('projects/add/', ProjectAdd.as_view(), name='project-add'),
    path('projects/list/', ProjectList.as_view(), name='project-list'),
    path('projects/published/', PublishedProjectList.as_view(), name='project-published'),
    path('projects/deleted/', DeletedProjectList.as_view(), name='project-deleted'),
    path('projects/details/', ProjectDetails.as_view(), name='project-details'),
    path('projects/update/', ProjectUpdate.as_view(), name='project-update'),
    path('projects/publish/', ChangeProjectPublishStatus.as_view(), name='project-publish'),
    path('projects/delete/<uuid:project_id>/', ProjectDelete.as_view(), name='project-delete'),
    path('projects/restore/', RestoreProject.as_view(), name='project-restore'),
]