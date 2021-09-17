from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_geo.versions.v1_0 import views as v1_0
from app_geo.versions.v1_0.serializers import CitySerializer, CitiesClusterSerializer
from backend.api_views import BaseAPIView
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Languages(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.Languages().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def custom_languages(request):
    if request.version in ['geo_1_0']:
        return v1_0.custom_languages(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Countries(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.Countries().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def custom_countries(request):
    if request.version in ['geo_1_0']:
        return v1_0.custom_countries(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Cities(BaseAPIView):
    serializer_class = CitySerializer

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.Cities().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class CitiesClusteredMap(BaseAPIView):
    serializer_class = CitiesClusterSerializer

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.CitiesClusteredMap().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def cities_suggestions(request):
    if request.version in ['geo_1_0']:
        return v1_0.cities_suggestions(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Geocode(APIView):
    @staticmethod
    def get(request):
        if request.version in ['geo_1_0']:
            return v1_0.geocode(request._request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)
