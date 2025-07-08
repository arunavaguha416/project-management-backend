# company/urls.py
from django.urls import path
from .views.company_view import *

# URL patterns for company-related API endpoints
urlpatterns = [
    path('add/', CompanyAdd.as_view(), name='company-add'),
    path('list/', CompanyList.as_view(), name='company-list'),
    path('details/', CompanyDetails.as_view(), name='company-details'),
    path('update/', CompanyUpdate.as_view(), name='company-update'),
    path('delete/<uuid:company_id>/', CompanyDelete.as_view(), name='company-delete'),
    path('restore/', RestoreCompany.as_view(), name='company-restore'),
]
