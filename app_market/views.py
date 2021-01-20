from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_market.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


class Vacancies(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            if kwargs.get('record_id', None):
                return JsonResponse({
                    "id": 1,
                    "title": "Фасовщик",
                    "description": "Осуществляет фасовку, дозировку  полуфабрикатов  и  готовой  продукции  или отдельных ее компонентов в тару - пакеты, пачки, банки, тубы, флаконы, ампулы, бутылки, бутыли, ящики, мешки и т.п. вручную как без взвешивания, отмера и оформления, так и с отмером по  заданному  объему, массе или количеству различных твердых, сыпучих, жидких и штучных товаров;",
                    "price": 500,
                    "isFavourite": True,
                    "shop": {
                        "id": 1,
                        "title": "Магнит",
                        "description": "Магазин Магнит на Сызранова 239",
                        "address": "Сызранова 239",
                        "walkTime": 1500000,
                        "logo": {
                            "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                            "title": "Магнит Лого",
                            "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                            "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                            "format": 2,
                            "type": 7,
                            "mimeType": "image/png"
                        }
                    },
                    "distributor": {
                        "id": 1,
                        "title": "Магнит",
                        "logo": {
                            "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                            "title": "Магнит Торговая Сеть Лого",
                            "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                            "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                            "format": 2,
                            "type": 7,
                            "mimeType": "image/png"
                        }
                    }
                }, safe=False)

            return JsonResponse([
                {"id": 1,
                 "title": "Фасовщик",
                 "description": "Осуществляет фасовку, дозировку  полуфабрикатов  и  готовой  продукции  или отдельных ее компонентов в тару - пакеты, пачки, банки, тубы, флаконы, ампулы, бутылки, бутыли, ящики, мешки и т.п. вручную как без взвешивания, отмера и оформления, так и с отмером по  заданному  объему, массе или количеству различных твердых, сыпучих, жидких и штучных товаров;",
                 "price": 500,
                 "isFavourite": True,
                 "requiredExperience": 0,
                 "employment": 0,
                 "shop": {
                     "id": 1,
                     "title": "Магнит",
                     "description": "Магазин Магнит на Сызранова 239",
                     "address": "Сызранова 239",
                     "walkTime": 1500000,
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": "Магнит Лого",
                         "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": "image/png"
                     }
                 },
                 "distributor": {
                     "id": 1,
                     "title": "Магнит",
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": "Магнит Торговая Сеть Лого",
                         "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": "image/png"
                     }
                 }
                 },
                {"id": 2,
                 "title": "Грузчик",
                 "description": "Осуществляет фасовку, дозировку  полуфабрикатов  и  готовой  продукции  или отдельных ее компонентов в тару - пакеты, пачки, банки, тубы, флаконы, ампулы, бутылки, бутыли, ящики, мешки и т.п. вручную как без взвешивания, отмера и оформления, так и с отмером по  заданному  объему, массе или количеству различных твердых, сыпучих, жидких и штучных товаров;",
                 "price": 600,
                 "isFavourite": False,
                 "requiredExperience": 0,
                 "employment": 0,
                 "shop": {
                     "id": 1,
                     "title": "Магнит",
                     "description": "Магазин Магнит на Крутцева 139",
                     "address": "Крутцева 139",
                     "walkTime": 2000000,
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": "Магнит Лого",
                         "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": "image/png"
                     }
                 },
                 "distributor": {
                     "id": 1,
                     "title": "Магнит",
                     "logo": {
                         "uuid": "ecaf71e2-c3c1-4e96-b88e-651410e4d3fc",
                         "title": "Магнит Торговая Сеть Лого",
                         "file": "/media/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "preview": "/media/preview/ecaf71e2-c3c1-4e96-b88e-651410e4d3fc.png",
                         "format": 2,
                         "type": 7,
                         "mimeType": "image/png"
                     }
                 }
                 }], safe=False)

            return v1_0.Vacancies().get(request, **kwargs)

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
