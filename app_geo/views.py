from django.http import JsonResponse
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


@api_view(['GET'])
def custom_countries(request):
    if request.version in ['geo_1_0']:
        return v1_0.custom_countries(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Cities(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            if kwargs.get('record_id', None):
                return JsonResponse(
                    {
                        "id": 1,
                        "name": "Москва",
                        "native": "Москва",
                        "country": {
                            "id": 1,
                            "isoCode": "RU",
                            "name": "Россия",
                            "native": "Россия",
                            "flag": {
                                "uuid": "c33350ea-3ba1-4eae-81bd-cdff1e9b12c9",
                                "title": "russia",
                                "file": "/media/c33350ea-3ba1-4eae-81bd-cdff1e9b12c9.png",
                                "preview": "/media/preview/c33350ea-3ba1-4eae-81bd-cdff1e9b12c9.png",
                                "format": 2,
                                "type": 8,
                                "mimeType": "image/png"
                            }
                        },
                        "region": {
                            "id": 1,
                            "name": "Московская область",
                            "native": "Московская область"
                        }
                    },
                    safe=False
                )
            return JsonResponse([
                {
                    "id": 1,
                    "name": "Москва",
                    "native": "Москва",
                    "country": {
                        "id": 1,
                        "isoCode": "RU",
                        "name": "Россия",
                        "native": "Россия",
                        "flag": {
                            "uuid": "c33350ea-3ba1-4eae-81bd-cdff1e9b12c9",
                            "title": "russia",
                            "file": "/media/c33350ea-3ba1-4eae-81bd-cdff1e9b12c9.png",
                            "preview": "/media/preview/c33350ea-3ba1-4eae-81bd-cdff1e9b12c9.png",
                            "format": 2,
                            "type": 8,
                            "mimeType": "image/png"
                        }
                    },
                    "region": {
                        "id": 1,
                        "name": "Московская область",
                        "native": "Московская область"
                    }
                }
            ], safe=False)
            # return v1_0.Cities().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Geocode(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return JsonResponse([
                {
                    "id": 1,
                    "name": "Москва",
                    "native": "Москва",
                    "country": {
                        "id": 1,
                        "isoCode": "RU",
                        "name": "Россия",
                        "native": "Россия",
                        "flag": {
                            "uuid": "c33350ea-3ba1-4eae-81bd-cdff1e9b12c9",
                            "title": "russia",
                            "file": "/media/c33350ea-3ba1-4eae-81bd-cdff1e9b12c9.png",
                            "preview": "/media/preview/c33350ea-3ba1-4eae-81bd-cdff1e9b12c9.png",
                            "format": 2,
                            "type": 8,
                            "mimeType": "image/png"
                        }
                    },
                    "region": {
                        "id": 1,
                        "name": "Московская область",
                        "native": "Московская область"
                    }
                }
            ], safe=False)
            # return v1_0.Cities().get(request, **kwargs)

        # raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
