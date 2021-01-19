from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from app_users.versions.v1_0 import views as v1_0
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


@api_view(['GET'])
@permission_classes([AllowAny])
def firebase_web_auth(request):
    if request.version in ['users_1_0']:
        return v1_0.firebase_web_auth(request._request)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


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

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthFirebase(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthFirebase.post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthRefreshToken(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthRefreshToken().post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


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

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.ReferenceCode.get(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Users(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.Users().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfile(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfile().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def patch(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfile().patch(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfileCareer(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCareer().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCareer().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def patch(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCareer().patch(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCareer().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfileUploads(APIView):
    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileUploads().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileUploads().delete(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfileSocials(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileSocials().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileSocials().delete(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfileDocuments(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def patch(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().patch(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Notifications(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.Notifications().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class NotificationsSettings(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.NotificationsSettings().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def put(request):
        if request.version in ['users_1_0']:
            return v1_0.NotificationsSettings().put(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
