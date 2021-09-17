from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_games.versions.v1_0 import views as v1_0
from app_users.permissions import IsAdminOrManager
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Prizes(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.Prizes().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class LikePrize(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.LikePrize().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.LikePrize().delete(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


@api_view(['GET'])
def bonus_progress_for_prizes(request):
    if request.version in ['games_1_0']:
        return v1_0.bonus_progress_for_prizes(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class PrizesDocuments(APIView):
    @staticmethod
    def get(request):
        if request.version in ['games_1_0']:
            return v1_0.PrizesDocuments().get(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class PrizeCards(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.PrizeCards().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class OpenPrizeCard(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.OpenPrizeCard().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class Tasks(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.Tasks().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class TasksCount(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.TasksCount().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminPrizes(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminPrizes().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminPrizes().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminPrize(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminPrize().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminPrize().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminPrize().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminGoodsCategories(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminGoodsCategories().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminGoodsCategories().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminGoodsCategory(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminGoodsCategory().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminGoodsCategory().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminGoodsCategory().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminTasks(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminTasks().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminTasks().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminTask(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminTask().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminTask().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminTask().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminUsersBonuses(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminUsersBonuses().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AdminUserBonuses(AdminUsersBonuses):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.AdminUserBonuses().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)
