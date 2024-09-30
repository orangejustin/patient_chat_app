from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('restart/', views.restart_conversation, name='restart_conversation'),
]
