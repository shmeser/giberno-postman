from channels.routing import ProtocolTypeRouter, URLRouter

from app_sockets import routing
from app_sockets.middlewares import token_auth_middleware_stack

application = ProtocolTypeRouter({
    'websocket': token_auth_middleware_stack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
