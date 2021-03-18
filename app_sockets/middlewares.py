from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from loguru import logger
from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def get_user(jwt):
    try:
        validated_token = JWTAuthentication().get_validated_token(jwt)
        return JWTAuthentication().get_user(validated_token)
    except Exception as e:
        logger.error(e)
        return AnonymousUser()


class TokenAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            query_string = scope.get('query_string')
            query_string = parse_qs(query_string.decode()) if isinstance(query_string, bytes) else dict()
            jwt = query_string.get('jwt')[0]
            scope['user'] = await get_user(jwt)
        except Exception as e:
            logger.error(e)
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)


def token_auth_middleware_stack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
