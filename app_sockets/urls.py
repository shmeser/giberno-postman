from django.urls import path

from app_sockets.views import index

urlpatterns = [
    path('index', index, name='index'),
]
