from django.urls import re_path

from app_sockets.consumers import GroupConsumer, Consumer

websocket_urlpatterns = [
    re_path(r'sockets/(?P<room_name>\w+)/(?P<id>\d+)$', GroupConsumer.as_asgi()),
    re_path(r'sockets', Consumer.as_asgi()),
]
