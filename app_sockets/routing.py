from django.conf.urls import url

from app_sockets.consumers import Consumer

websocket_urlpatterns = [
    url('sockets', Consumer.as_asgi()),
]
