from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_market.versions.v1_0 import views as v1_0
from app_market.versions.v1_0.serializers import DistributorSerializer, ProfessionSerializer, ShiftsSerializer, \
    ShopSerializer, SkillSerializer, VacanciesSerializer, QRCodeSerializer, UserShiftSerializer
from backend.api_views import BaseAPIView
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


class Distributors(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', DistributorSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Distributors().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Shops(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ShopSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Shops().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Vacancies(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', VacanciesSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Vacancies().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Shifts(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ShiftsSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Shifts().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class CheckUserShiftByManagerOrSecurityAPIView(BaseAPIView):
    serializer_class = QRCodeSerializer

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', UserShiftSerializer)})
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.CheckUserShiftByManagerOrSecurityAPIView().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class VacanciesStats(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacanciesStats().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


@api_view(['GET'])
def vacancies_suggestions(request):
    if request.version in ['market_1_0']:
        return v1_0.vacancies_suggestions(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


@api_view(['POST'])
def review_vacancy(request, **kwargs):
    if request.version in ['market_1_0']:
        return v1_0.review_vacancy(request._request, **kwargs)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class LikeVacancy(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.LikeVacancy().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.LikeVacancy().delete(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Professions(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ProfessionSerializer)})
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
    @swagger_auto_schema(responses={200: openapi.Response('response description', SkillSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Skills().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
