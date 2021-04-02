from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from app_chats.versions.v1_0.serializers import ChatsSerializer
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException
from .versions.v1_0 import views as v1_0


class Chats(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ChatsSerializer)})
    def get(request, **kwargs):
        if request.version in ['chats_1_0']:
            return v1_0.Chats().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Messages(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ChatsSerializer)})
    def get(request, **kwargs):
        if request.version in ['chats_1_0']:
            return v1_0.Messages().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)