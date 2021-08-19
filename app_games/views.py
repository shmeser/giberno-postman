from rest_framework.decorators import api_view
from rest_framework.views import APIView

from app_games.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Prizes(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.Prizes().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class LikePrize(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.LikePrize().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.LikePrize().delete(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


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

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class PrizeCards(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.PrizeCards().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class OpenPrizeCard(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.OpenPrizeCard().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Tasks(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.Tasks().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class TasksCount(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['games_1_0']:
            return v1_0.TasksCount().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminPrizes(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminPrizes().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminTasks(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminTasks().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminUsersBonuses(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['market_1_0']:
            return v1_0.AdminUsersBonuses().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
