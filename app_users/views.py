from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.permissions import IsAdmin
from app_users.versions.v1_0 import views as v1_0
from app_users.versions.v1_0.serializers import FirebaseAuthRequestDescriptor, FirebaseAuthResponseDescriptor, \
    RefreshTokenSerializer, CreateManagerByAdminSerializer, ProfileSerializer, UsernameSerializer, \
    UsernameWithPasswordSerializer, ManagerAuthenticateResponseForSwagger, PasswordSerializer, \
    EditManagerProfileSerializer, NotificationSerializer, NotificationsSettingsSerializer, CareerSerializer, \
    DocumentSerializer, SocialSerializer
from backend.api_views import BaseAPIView
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException

SWAGGER_RESPONSE_DESCRIPTION = 'response description'


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


class AuthVk(BaseAPIView):
    permission_classes = (AllowAny,)

    @staticmethod
    @swagger_auto_schema(
        responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, FirebaseAuthResponseDescriptor)})
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthVk(request).post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthFirebase(BaseAPIView):
    permission_classes = (AllowAny,)
    serializer_class = FirebaseAuthRequestDescriptor

    @staticmethod
    @swagger_auto_schema(
        responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, FirebaseAuthResponseDescriptor)})
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthFirebase.post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthRefreshToken(BaseAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RefreshTokenSerializer

    @staticmethod
    @swagger_auto_schema(
        responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, FirebaseAuthResponseDescriptor)})
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
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, ProfileSerializer)})
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.Users().get(request, **kwargs)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfile(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, ProfileSerializer)})
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
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, CareerSerializer)})
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCareer().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, CareerSerializer)})
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCareer().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, CareerSerializer)})
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
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, MediaSerializer)})
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
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, SocialSerializer)})
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
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, DocumentSerializer)})
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, DocumentSerializer)})
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, DocumentSerializer)})
    def patch(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().patch(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, DocumentSerializer)})
    def delete(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocuments().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class Notifications(APIView):
    @staticmethod
    @swagger_auto_schema(responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, NotificationSerializer)})
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.Notifications().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class NotificationsSettings(APIView):
    @staticmethod
    @swagger_auto_schema(
        responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, NotificationsSettingsSerializer)})
    def get(request):
        if request.version in ['users_1_0']:
            return v1_0.NotificationsSettings().get(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    @swagger_auto_schema(
        responses={200: openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, NotificationsSettingsSerializer)})
    def put(request):
        if request.version in ['users_1_0']:
            return v1_0.NotificationsSettings().put(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def read_notification(request, **kwargs):
    if request.version in ['users_1_0']:
        return v1_0.read_notification(request._request, **kwargs)
    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


# PUSH SUBSCRIBE
@api_view(['POST'])
def push_subscribe(request, **kwargs):
    if request.version in ['users_1_0']:
        return v1_0.push_subscribe(request._request)

    raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


# PUSH UNSUBSCRIBE
class PushUnsubscribe(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.PushUnsubscribe.post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


# MANAGERS RELATED VIEWS
class CreateManagerByAdminAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = CreateManagerByAdminSerializer
    response_description = openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, ProfileSerializer)

    @transaction.atomic
    @swagger_auto_schema(responses={200: response_description})
    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.CreateManagerByAdminAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class GetManagerByUsernameAPIView(BaseAPIView):
    permission_classes = []
    serializer_class = UsernameSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.GetManagerByUsernameAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthenticateManagerAPIView(BaseAPIView):
    permission_classes = []
    serializer_class = UsernameWithPasswordSerializer

    response_description = openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, ManagerAuthenticateResponseForSwagger)

    @swagger_auto_schema(responses={200: response_description})
    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.AuthenticateManagerAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class ChangeManagerPasswordAPIView(BaseAPIView):
    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.ChangeManagerPasswordAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class EditManagerProfileView(BaseAPIView):
    serializer_class = EditManagerProfileSerializer

    response_description = openapi.Response(SWAGGER_RESPONSE_DESCRIPTION, ProfileSerializer)

    @swagger_auto_schema(responses={200: response_description})
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.EditManagerProfileView().patch(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)
