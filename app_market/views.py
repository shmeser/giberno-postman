from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_market.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


class Distributors(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Distributors().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Shops(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Shops().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Vacancies(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            mime_type = "image/png"
            title = "Магнит"
            if kwargs.get('record_id', None):
                return JsonResponse({
                    "id": 1,
                    "title": "Фасовщик",
                    "description": "Осуществляет фасовку, дозировку  полуфабрикатов  и  готовой  продукции  или отдельных ее компонентов в тару - пакеты, пачки, банки, тубы, флаконы, ампулы, бутылки, бутыли, ящики, мешки и т.п. вручную как без взвешивания, отмера и оформления, так и с отмером по  заданному  объему, массе или количеству различных твердых, сыпучих, жидких и штучных товаров;",
                    "price": 500,
                    "isFavourite": True,
                    "shop": {
                        "id": 1,
                        "title": title,
                        "description": "Магазин на Сызранова 239",
                        "address": "Сызранова 239",
                        "walkTime": 1500000,
                        "logo": {
                            "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                            "title": "Магнит Лого",
                            "file": "/media/ecaf71e2-c3c1-4e96-b88e-652410e4d3fc.png",
                            "preview": "/media/preview/ecaf71e2-c3c1-4496-b88e-651410e4d3fc.png",
                            "format": 2,
                            "type": 7,
                            "mimeType": mime_type
                        }
                    },
                    "distributor": {
                        "id": 1,
                        "title": title,
                        "logo": {
                            "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                            "title": " Торговая Сеть Лого",
                            "file": "/media/ecaf72e2-c3c1-4e96-b88e-651410e4d3fc.png",
                            "preview": "/media/preview/ecaf71e2-c3c1-4e66-b88e-651410e4d3fc.png",
                            "format": 2,
                            "type": 7,
                            "mimeType": mime_type
                        }
                    }
                }, safe=False)

            return JsonResponse([
                {"id": 1,
                 "title": "Фасовщик",
                 "description": "Осуществляет фасовку",
                 "price": 500,
                 "isFavourite": True,
                 "isHot": True,
                 "requiredExperience": 0,
                 "employment": 0,
                 "shop": {
                     "id": 1,
                     "title": "Магнит У дома",
                     "description": "Магазин на Сызранова 239",
                     "address": "Сызранова 239",
                     "walkTime": 1500000,
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": " Лого",
                         "file": "/media/ecad71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e86-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": mime_type
                     }
                 },
                 "distributor": {
                     "id": 1,
                     "title": title,
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": "Торговая Сеть Лого",
                         "file": "/media/ecaf71e5-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e3-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": mime_type
                     }
                 }
                 },
                {"id": 2,
                 "title": "Грузчик",
                 "description": "Грузит товары",
                 "price": 600,
                 "isFavourite": False,
                 "isHot": False,
                 "requiredExperience": 0,
                 "employment": 0,
                 "shop": {
                     "id": 1,
                     "title": title,
                     "description": "Магазин на Крутцева 139",
                     "address": "Крутцева 139",
                     "walkTime": 2000000,
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": " Лого",
                         "file": "/media/ecaf71e2-c3d1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": mime_type
                     }
                 },
                 "distributor": {
                     "id": 1,
                     "title": title,
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": " Торговая Сеть Лого",
                         "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": mime_type
                     }
                 }
                 }], safe=False)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Professions(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Professions().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


@api_view(['POST'])
def suggest_profession(request):
    if request.version in ['market_1_0']:
        return v1_0.suggest_profession(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Skills(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Skills().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
