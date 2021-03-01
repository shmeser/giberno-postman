from django.urls import re_path

from app_sockets.consumers import Consumer

websocket_urlpatterns = [
    re_path(r'sockets/(?P<room_name>\w+)/(?P<id>\d+)$', Consumer.as_asgi()),
]
