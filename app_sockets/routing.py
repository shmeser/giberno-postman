from django.urls import re_path

from app_sockets.consumers import GroupConsumer, Consumer

websocket_urlpatterns = [
    # Подключение к роутам, учитывая версионность
    # re_path(r'v(?P<version>[0-9]{1,2}.[0-9]{1,2})/sockets/(?P<room_name>\w+)/(?P<id>\d+)$', GroupConsumer.as_asgi()),
    re_path(r'v(?P<version>[0-9]{1,2}.[0-9]{1,2})/sockets', Consumer.as_asgi()),
]
