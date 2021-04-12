from rest_framework.views import APIView

from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException
from .versions.v1_0 import views as v1_0


class Chats(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['chats_1_0']:
            return v1_0.Chats().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Messages(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['chats_1_0']:
            return v1_0.Messages().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['chats_1_0']:
            return v1_0.Messages().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class ReadMessages(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['chats_1_0']:
            return v1_0.ReadMessages().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
