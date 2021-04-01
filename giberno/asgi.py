import os

from channels.routing import ProtocolTypeRouter, URLRouter
# import django
from django.core.asgi import get_asgi_application

from app_sockets import routing
from app_sockets.middlewares import token_auth_middleware_stack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giberno.settings')
# django.setup()
django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    'websocket': token_auth_middleware_stack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
