from rest_framework.views import APIView

from app_games.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Prizes(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['prizes_1_0']:
            return v1_0.Prizes().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class LikePrize(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['prizes_1_0']:
            return v1_0.LikePrize().post(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['prizes_1_0']:
            return v1_0.LikePrize().delete(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class PrizesDocuments(APIView):
    @staticmethod
    def get(request):
        if request.version in ['prizes_1_0']:
            return v1_0.PrizesDocuments().get(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class PrizeCards(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['prizes_1_0']:
            return v1_0.PrizeCards().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Tasks(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['prizes_1_0']:
            return v1_0.Tasks().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
