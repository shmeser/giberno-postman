from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from app_users.versions.v1_0 import views as v1_0
from backend.errors.http_exception import HttpException


def firebase_web_auth(request):
    if request.version in ['users_1_0']:
        return v1_0.firebase_web_auth(request)
    raise HttpException(status_code=status.HTTP_404_NOT_FOUND, detail="Метод не найден")


@login_required
def social_web_auth(request):
    if request.version in ['users_1_0']:
        return v1_0.social_web_auth(request)
    raise HttpException(status_code=status.HTTP_404_NOT_FOUND, detail="Метод не найден")


def login(request):
    if request.version in ['users_1_0']:
        return v1_0.login(request)
    raise HttpException(status_code=status.HTTP_404_NOT_FOUND, detail="Метод не найден")


class AuthFirebase(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthFirebase.post(request)

        raise HttpException(status_code=status.HTTP_404_NOT_FOUND, detail="Метод не найден")


class AuthRefreshToken(APIView):
    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthRefreshToken().post(request)

        raise HttpException(status_code=status.HTTP_404_NOT_FOUND, detail="Метод не найден")


class Users(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            pass
        return JsonResponse({
        })
