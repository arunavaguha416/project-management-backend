from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views.authentication_view import *

urlpatterns = [    
    path('register/', Registration.as_view(), name='register'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', Logout.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # api/token/refresh/ does not require a separate view function because TokenRefreshView is a pre-built view provided by the djangorestframework-simplejwt library. 
    # It handles the logic for refreshing JWT access tokens using a valid refresh token, so you don’t need to write a custom view function for it.
]