from rest_framework.views import APIView

from app_games.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Prizes(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['geo_1_0']:
            return v1_0.Prizes().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
