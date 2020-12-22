from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_geo.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


class Languages(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.Languages().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


@api_view(['GET'])
def custom_languages(request):
    if request.version in ['geo_1_0']:
        return v1_0.custom_languages(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Countries(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.Countries().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
