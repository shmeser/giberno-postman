from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from app_users.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException


@api_view(['GET'])
@permission_classes([AllowAny])
def firebase_web_auth(request):
    if request.version in ['users_1_0']:
        return v1_0.firebase_web_auth(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")


@login_required
def social_web_auth(request):
    return render(request, 'app_users/home.html', context={'user': request.user})


def login(request):
    return render(request, 'app_users/login.html')


class AuthVk(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthVk(request).post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")


class AuthFirebase(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthFirebase.post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")


class AuthRefreshToken(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthRefreshToken().post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")


class ReferenceCode(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        elif self.request.method == "POST":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.ReferenceCode.post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")

    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.ReferenceCode.get(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")


class Users(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.Users().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")


class MyProfile(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfile().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")

    @staticmethod
    def patch(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfile().patch(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail="Метод не найден")
