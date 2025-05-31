from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views.authentication_view import *

urlpatterns = [    
    path('api/register/', Registration.as_view(), name='register'),
    path('api/login/', Login.as_view(), name='login'),
    path('api/logout/', Logout.as_view(), name='logout'),
    path('api/profile/', UserProfileView.as_view(), name='profile'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # api/token/refresh/ does not require a separate view function because TokenRefreshView is a pre-built view provided by the djangorestframework-simplejwt library. 
    # It handles the logic for refreshing JWT access tokens using a valid refresh token, so you don’t need to write a custom view function for it.
]