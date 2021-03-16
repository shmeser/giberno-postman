from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app_feedback.versions.v1_0.serializers import POSTReviewSerializer, ReviewModelSerializer
from app_market.versions.v1_0 import views as v1_0
from app_market.versions.v1_0.serializers import DistributorsSerializer, ProfessionSerializer, ShiftsSerializer, \
    ShopSerializer, SkillSerializer, VacanciesSerializer, QRCodeSerializer, UserShiftSerializer, \
    VacanciesClusterSerializer, VacanciesListForManagerSerializer, SingleVacancyForManagerSerializer, \
    AppliedUsersByVacancyForManagerSerializer, ApplyToVacancyResponseSerializer
from app_users.permissions import IsManager, IsSelfEmployed
from backend.api_views import BaseAPIView
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


class Distributors(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', DistributorsSerializer)})
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


class ApplyToVacancyAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ApplyToVacancyResponseSerializer)})
    def get(request, **kwargs):
        '''
        Откликнуться на вакансию
        '''
        if request.version in ['market_1_0']:
            return v1_0.ApplyToVacancyAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={204: openapi.Response('No Content')})
    def delete(request, **kwargs):
        '''
        Удалить отклик на вакансию
        '''
        if request.version in ['market_1_0']:
            return v1_0.ApplyToVacancyAPIView().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class GetVacanciesByManagerShopAPIView(BaseAPIView):
    """
    Получение списка вакансий, которые закреплены за  магазином\магазинами менеджера
    возможные query параметры :
    available_from=год-месяц-день
    Это дата с которой вакансия доступна
    """
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', VacanciesListForManagerSerializer)})
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.GetVacanciesByManagerShopAPIView().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class GetSingleVacancyForManagerAPIView(BaseAPIView):
    """
    Просмотр конкретной вакансии со стороны менеджера
    """
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', SingleVacancyForManagerSerializer)})
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.GetSingleVacancyForManagerAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class GetAppliedUsersByVacancyForManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description',
                                                          AppliedUsersByVacancyForManagerSerializer)})
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.GetAppliedUsersByVacancyForManagerAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class VacanciesClusteredMap(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', VacanciesClusterSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacanciesClusteredMap().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Shifts(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ShiftsSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Shifts().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class UserShiftsAPIView(BaseAPIView):
    """
    Возвращает список смен пользователя
    можно фильтровать по статусу смены.
    """
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', UserShiftSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.UserShiftsAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class CheckUserShiftByManagerOrSecurityAPIView(BaseAPIView):
    """
    Проверка QR CODE со стороны охранника или менеджера
    Если проверяющий -охранник, то статус смены остается неизменным
    """
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
def similar_vacancies(request, **kwargs):
    if request.version in ['market_1_0']:
        return v1_0.similar_vacancies(request._request, **kwargs)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


@api_view(['GET'])
def vacancies_suggestions(request):
    if request.version in ['market_1_0']:
        return v1_0.vacancies_suggestions(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class VacancyReviewsAPIView(BaseAPIView):
    serializer_class = POSTReviewSerializer

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        '''
        Оставить отзыв о вакансии
        '''
        if request.version in ['market_1_0']:
            return v1_0.VacancyReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ReviewModelSerializer)})
    def get(request, **kwargs):
        '''
        Получить список отзывов о вакансии
        '''
        if request.version in ['market_1_0']:
            return v1_0.VacancyReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class ShopReviewsAPIView(BaseAPIView):
    serializer_class = POSTReviewSerializer

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        '''
        Oставить отзыв о магазине
        '''
        if request.version in ['market_1_0']:
            return v1_0.ShopReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ReviewModelSerializer)})
    def get(request, **kwargs):
        '''
        Получить список отзывов о магазине
        '''
        if request.version in ['market_1_0']:
            return v1_0.ShopReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class DistributorReviewsAPIView(BaseAPIView):
    serializer_class = POSTReviewSerializer

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        '''
        Оставить отзыв к торговой сети
        '''
        if request.version in ['market_1_0']:
            return v1_0.DistributorReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ReviewModelSerializer)})
    def get(request, **kwargs):
        '''
        Получить список отзывов торговой сети
        '''
        if request.version in ['market_1_0']:
            return v1_0.DistributorReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class ToggleLikeVacancy(APIView):
    """
    Лайкнуть/отлайкнуть. работает один и тот же метод. Если нет лайка - добавит. Если есть - удалит
    """

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.ToggleLikeVacancy().post(request, **kwargs)

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
