from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app_feedback.versions.v1_0.serializers import POSTReviewSerializer, ReviewModelSerializer, \
    POSTReviewByManagerSerializer
from app_market.versions.v1_0 import views as v1_0
from app_market.versions.v1_0.serializers import ProfessionSerializer, ShiftsSerializer, \
    QRCodeSerializer, UserShiftSerializer
from app_users.permissions import IsManager, IsSelfEmployed, IsAdminOrManager, IsManagerOrSecurity
from backend.api_views import BaseAPIView
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Distributors(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Distributors().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Shops(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Shops().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Vacancies(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Vacancies().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShiftAppeals(BaseAPIView):
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    def get(request, **kwargs):
        """ Список своих откликов на рабочие смены """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppeals().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        """ Откликнуться на рабочую смену """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppeals().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def put(request, **kwargs):
        """ Редактирование отклика """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppeals().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShiftAppealCancel(BaseAPIView):
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    def post(request, **kwargs):
        """
        Отменить отклик на рабочую смену
        """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppealCancel().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ActiveVacanciesWithAppliersByDateForManagerListAPIView(BaseAPIView):
    """
    Получение списка вакансий, которые закреплены за  магазином\магазинами менеджера
    возможные query параметры :
    offset : int
    limit : int
    current_date : timestamp (int)
    """
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.ActiveVacanciesWithAppliersByDateForManagerListAPIView().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacancyByManagerRetrieveAPIView(BaseAPIView):
    """
    Просмотр конкретной вакансии (среди прикрепленных к своему магазину) со стороны менеджера

    """
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacancyByManagerRetrieveAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacanciesActiveDatesForManagerListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    """
    Для менеджеров : Список дат с которых вакансии доступны 
    параметры фильтрации:
    calendar_from 
    calendar_to
    """

    @staticmethod
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacanciesActiveDatesForManagerListAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class SingleVacancyActiveDatesForManagerListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    """
    Запрос для получения активных дат (аналогичный /market/managers/vacancies/active_dates , 
    только для конкретной вакансии)
    параметры фильтрации:
    calendar_from 
    calendar_to
    """

    @staticmethod
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.SingleVacancyActiveDatesForManagerListAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacancyShiftsWithAppealsListForManagerAPIView(BaseAPIView):
    """
    Просмотр Списка откликнувшихся на вакансию со стороны менеджера
    Параметры : current_date
    """
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacancyShiftsWithAppealsListForManagerAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class GetSingleAppealForManagerAPIView(BaseAPIView):
    """
    Просмотр конкретного отклика со стороны менеджера
    """

    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def get(request, *args, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.GetSingleAppealForManagerAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacanciesClusteredMap(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacanciesClusteredMap().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Shifts(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Shifts().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class UserShiftsListAPIView(BaseAPIView):
    """
    Возвращает список смен пользователя
    можно фильтровать по статусу смены.
    """
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.UserShiftsListAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class UserShiftsRetrieveAPIView(BaseAPIView):
    """
    получение смены пользователя по id
    """
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.UserShiftsRetrieveAPIView().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class CheckUserShiftByManagerOrSecurityAPIView(BaseAPIView):
    """
    Проверка QR CODE со стороны охранника или менеджера
    Если проверяющий -охранник, то статус смены остается неизменным
    """
    permission_classes = [IsManagerOrSecurity]
    serializer_class = QRCodeSerializer

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.CheckUserShiftByManagerOrSecurityAPIView().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class GetDocumentsForShift(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.GetDocumentsForShift().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacanciesStats(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacanciesStats().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacanciesDistributors(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.VacanciesDistributors().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def similar_vacancies(request, **kwargs):
    if request.version in ['market_1_0']:
        return v1_0.similar_vacancies(request._request, **kwargs)
    raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def vacancies_suggestions(request):
    if request.version in ['market_1_0']:
        return v1_0.vacancies_suggestions(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class VacancyReviewsAPIView(BaseAPIView):
    serializer_class = POSTReviewSerializer

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        """
        Оставить отзыв о вакансии
        """
        if request.version in ['market_1_0']:
            return v1_0.VacancyReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ReviewModelSerializer)})
    def get(request, **kwargs):
        """
        Получить список отзывов о вакансии
        """
        if request.version in ['market_1_0']:
            return v1_0.VacancyReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShopReviewsAPIView(BaseAPIView):
    serializer_class = POSTReviewSerializer

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        """
        Oставить отзыв о магазине
        """
        if request.version in ['market_1_0']:
            return v1_0.ShopReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ReviewModelSerializer)})
    def get(request, **kwargs):
        """
        Получить список отзывов о магазине
        """
        if request.version in ['market_1_0']:
            return v1_0.ShopReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class DistributorReviewsAPIView(BaseAPIView):
    serializer_class = POSTReviewSerializer

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        """
        Оставить отзыв к торговой сети
        """
        if request.version in ['market_1_0']:
            return v1_0.DistributorReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ReviewModelSerializer)})
    def get(request, **kwargs):
        """
        Получить список отзывов торговой сети
        """
        if request.version in ['market_1_0']:
            return v1_0.DistributorReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class SelfEmployedUserReviewsByAdminOrManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = POSTReviewByManagerSerializer

    @staticmethod
    def post(request, **kwargs):
        """
        Отзывы на самозанятого (оставляют Администраторы / менеджеры)
        """
        if request.version in ['market_1_0']:
            return v1_0.SelfEmployedUserReviewsByAdminOrManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def get(request, **kwargs):
        """
            Получить список отзывов на самозанятого (получают Администраторы / менеджеры))
        """
        if request.version in ['market_1_0']:
            return v1_0.SelfEmployedUserReviewsByAdminOrManagerAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmAppealByManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def post(request, **kwargs):
        """
            подтвердить отклик на вакансию (подтверждают Администраторы / менеджеры))
        """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmAppealByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class RejectAppealByManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def post(request, **kwargs):
        """
            Отклонить отклик на вакансию (отклоняют Администраторы / менеджеры))
        """
        if request.version in ['market_1_0']:
            return v1_0.RejectAppealByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ToggleLikeVacancy(APIView):
    """
        Лайкнуть/отлайкнуть. работает один и тот же метод. Если нет лайка - добавит. Если есть - удалит
    """

    @staticmethod
    @swagger_auto_schema(responses={204: 'No Content'})
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.ToggleLikeVacancy().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Professions(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response('response description', ProfessionSerializer)})
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Professions().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['POST'])
def suggest_profession(request):
    if request.version in ['market_1_0']:
        return v1_0.suggest_profession(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Skills(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Skills().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class MarketDocuments(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.MarketDocuments().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShiftForManagers(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """
            Смена (получают Администраторы / менеджеры))
        """
        if request.version in ['market_1_0']:
            return v1_0.ShiftForManagers().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShiftAppealsForManagers(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """
            Отклики на смену (получают Администраторы / менеджеры))
        """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppealsForManagers().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmedWorkers(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """
            Список одобренных работников (получают Администраторы / менеджеры ) )
        """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmedWorkers().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmedWorkersVacancies(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """
            Список вакансий одобренных работников (получают Администраторы / менеджеры ) )
        """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmedWorkersVacancies().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmedWorkersDates(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """
            Список дат для смен одобренных работников (получают Администраторы / менеджеры ) )
        """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmedWorkersDates().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)
