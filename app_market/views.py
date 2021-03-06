from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app_market.versions.v1_0 import views as v1_0
from app_users.permissions import IsManager, IsSelfEmployed, IsAdminOrManager, IsSecurity
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


class ShiftAppealComplete(BaseAPIView):
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    def post(request, **kwargs):
        """
        закрыть смену после того как она была завершена (когда отображается таймер 15 минут чтоб уйти из зоны)
        """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppealComplete().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ActiveVacanciesWithAppliersByDateForManagerListAPIView(BaseAPIView):
    """
    Получение списка вакансий, которые закреплены за  магазином / магазинами менеджера
    возможные query параметры :
    offset : int
    limit : int
    current_date : timestamp (int)
    """
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def get(request):
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


class SingleVacancyActiveDatesForManager(BaseAPIView):
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


class GetDocumentsForPartner(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.GetDocumentsForPartner().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class PartnersShopDocuments(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.PartnersShopDocuments().get(request, **kwargs)
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
    @staticmethod
    def post(request, **kwargs):
        """
        Оставить отзыв о вакансии
        """
        if request.version in ['market_1_0']:
            return v1_0.VacancyReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def get(request, **kwargs):
        """
        Получить список отзывов о вакансии
        """
        if request.version in ['market_1_0']:
            return v1_0.VacancyReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShopReviewsAPIView(BaseAPIView):
    @staticmethod
    def post(request, **kwargs):
        """
        Oставить отзыв о магазине
        """
        if request.version in ['market_1_0']:
            return v1_0.ShopReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def get(request, **kwargs):
        """
        Получить список отзывов о магазине
        """
        if request.version in ['market_1_0']:
            return v1_0.ShopReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class DistributorReviewsAPIView(BaseAPIView):
    @staticmethod
    def post(request, **kwargs):
        """
        Оставить отзыв к торговой сети
        """
        if request.version in ['market_1_0']:
            return v1_0.DistributorReviewsAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def get(request, **kwargs):
        """
        Получить список отзывов торговой сети
        """
        if request.version in ['market_1_0']:
            return v1_0.DistributorReviewsAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class SelfEmployedUserReviewsByAdminOrManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

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
        """ Получить список отзывов на самозанятого (получают Администраторы / менеджеры) """
        if request.version in ['market_1_0']:
            return v1_0.SelfEmployedUserReviewsByAdminOrManagerAPIView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmAppealByManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def post(request, **kwargs):
        """ подтвердить отклик на вакансию (подтверждают Администраторы / менеджеры) """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmAppealByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class RejectAppealByManagerAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def post(request, **kwargs):
        """ Отклонить отклик на вакансию (отклоняют Администраторы / менеджеры) """
        if request.version in ['market_1_0']:
            return v1_0.RejectAppealByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ToggleLikeVacancy(APIView):
    """
        Лайкнуть/отлайкнуть. работает один и тот же метод. Если нет лайка - добавит. Если есть - удалит
    """

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.ToggleLikeVacancy().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Professions(APIView):
    @staticmethod
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
        """ Смена (получают Администраторы / менеджеры) """
        if request.version in ['market_1_0']:
            return v1_0.ShiftForManagers().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShiftAppealsForManagers(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """ Отклики на смену (получают Администраторы / менеджеры) """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppealsForManagers().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmedWorkers(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """ Список одобренных работников (получают Администраторы / менеджеры ) """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmedWorkers().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmedWorkersProfessions(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """ Список вакансий одобренных работников (получают Администраторы / менеджеры ) """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmedWorkersProfessions().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ConfirmedWorkersDates(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        """ Список дат для смен одобренных работников (получают Администраторы / менеджеры ) """
        if request.version in ['market_1_0']:
            return v1_0.ConfirmedWorkersDates().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class PushSettingsForConfirmedWorkers(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @staticmethod
    def put(request, **kwargs):
        """ Настройки уведомлений для одобренных работников (получают Администраторы / менеджеры ) """
        if request.version in ['market_1_0']:
            return v1_0.PushSettingsForConfirmedWorkers().put(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class QRView(APIView):
    permission_classes = [IsAuthenticated, IsSelfEmployed]

    @staticmethod
    def get(request, **kwargs):
        """ Информация по ближайшим/текущим сменам """
        if request.version in ['market_1_0']:
            return v1_0.QRView().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class CheckPassByManagerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Получить объект пропуска """
        if request.version in ['market_1_0']:
            return v1_0.CheckPassByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AllowPassByManagerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Одобрить пропуск со стороны менеджера """
        if request.version in ['market_1_0']:
            return v1_0.AllowPassByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class CheckPassBySecurityAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSecurity]

    @staticmethod
    def post(request, **kwargs):
        """ Сканирование qr охранников """
        if request.version in ['market_1_0']:
            return v1_0.CheckPassBySecurityAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class RefusePassBySecurityAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSecurity]

    @staticmethod
    def post(request, **kwargs):
        """ Отказать в пропуске со стороны охранника """
        if request.version in ['market_1_0']:
            return v1_0.RefusePassBySecurityAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class RefusePassByManagerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Отказать в пропуске со стороны менеджера """
        if request.version in ['market_1_0']:
            return v1_0.RefusePassByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class FireByManagerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Увольнение самозанятого """
        if request.version in ['market_1_0']:
            return v1_0.FireByManagerAPIView().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class CancelFiringByManager(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Отмена увольнения самозанятого """
        if request.version in ['market_1_0']:
            return v1_0.CancelFiringByManager().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ProlongByManager(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Продление смены самозанятого """
        if request.version in ['market_1_0']:
            return v1_0.ProlongByManager().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ShiftAppealCompleteByManager(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    @staticmethod
    def post(request, **kwargs):
        """ Завершить смену менеджером """
        if request.version in ['market_1_0']:
            return v1_0.ShiftAppealCompleteByManager().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['POST'])
def work_location(request, **kwargs):
    if request.version in ['market_1_0']:
        return v1_0.work_location(request._request, **kwargs)
    raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Partners(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Partners().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class PartnersCategories(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.PartnersCategories().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Achievements(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Achievements().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Advertisements(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Advertisements().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Orders(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Orders().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Orders().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Coupons(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Coupons().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Finances(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.Finances().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def get_my_money(request):
    if request.version in ['market_1_0']:
        return v1_0.get_my_money(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminShops(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShops().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShops().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminShop(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShop().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShop().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShop().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminVacancies(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminVacancies().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminVacancies().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminVacancy(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminVacancy().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminVacancy().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminVacancy().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminAppeals(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminAppeals().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminAppeals().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminAppeal(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminAppeal().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminAppeal().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminAppeal().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminShifts(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShifts().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShifts().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminShift(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShift().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShift().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminShift().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminProfessions(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminProfessions().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminProfessions().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminProfession(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminProfession().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminProfession().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminProfession().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminPositions(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminPositions().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminPositions().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminPosition(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminPosition().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminPosition().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminPosition().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminDistributors(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminDistributors().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminDistributors().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminDistributor(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminDistributor().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminDistributor().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminDistributor().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminStructures(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminStructures().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminStructures().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminStructure(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminStructure().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminStructure().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminStructure().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminCoupons(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminCoupons().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminCoupons().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminCoupon(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminCoupon().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminCoupon().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminCoupon().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
