import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Fetch Django ASGI application early to ensure AppRegistry is populated
# before importing consumers and AuthMiddlewareStack that may import ORM
# models.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giberno.settings')
django_asgi_app = get_asgi_application()
# Подгружаем роутинг и авторизацию для сокетов после инициализации asgi
from app_sockets import routing
from app_sockets.middlewares import token_auth_middleware_stack

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
