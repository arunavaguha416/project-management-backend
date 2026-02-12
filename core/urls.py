from django.urls import path
from core.views import GlobalAIChatView

urlpatterns = [
    path("ai/chat/", GlobalAIChatView.as_view()),
]
