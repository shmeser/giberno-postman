from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from app_users.permissions import IsAdmin, IsAdminOrManager
from app_users.versions.v1_0 import views as v1_0
from app_users.versions.v1_0.serializers import FirebaseAuthRequestDescriptor, RefreshTokenSerializer, \
    CreateManagerByAdminSerializer, UsernameSerializer, \
    UsernameWithPasswordSerializer, PasswordSerializer, \
    EditManagerProfileSerializer
from backend.api_views import BaseAPIView
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


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
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthVk(request).post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthFirebase(BaseAPIView):
    permission_classes = (AllowAny,)
    serializer_class = FirebaseAuthRequestDescriptor

    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AuthFirebase.post(request)

        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthRefreshToken(BaseAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RefreshTokenSerializer

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


class MyProfileDocument(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocument().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def patch(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocument().patch(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileDocument().delete(request, **kwargs)
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
    """
    ???????????????? ?????????????????? ?????????? ??????????.???????????? ????????????????????????????.
    ?????????? ?? ???????????? ?????? ?????????????? ?????????? ?????????????????? ?????????????????????????? ???????????????????????? ?????? ???? e-mail
    ?? ???????????? ?????? ????????????????.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = CreateManagerByAdminSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.CreateManagerByAdminAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class GetManagerByUsernameAPIView(BaseAPIView):
    """
    ???????? ???????????? ???? ?????????????? ??????????????????
    """
    permission_classes = []
    serializer_class = UsernameSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.GetManagerByUsernameAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthenticateManagerAPIView(BaseAPIView):
    """
    ???????? ???????????? ?? ???????????? ???? ?????????????? ??????????????????

    """
    permission_classes = []
    serializer_class = UsernameWithPasswordSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.AuthenticateManagerAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class ChangeManagerPasswordAPIView(BaseAPIView):
    """
    ?????????????????? ???????????? ???? ?????????????? ??????????????????.
    (?? ???????????? ?????????????? ?????????? ???????????????????????? ???????????????????????? ?????????????? ?????????????????????? ????????????.)
    """
    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.ChangeManagerPasswordAPIView().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class EditManagerProfileView(BaseAPIView):
    """
    ???????????????????????????? ?????????????? ?????????????????? : ???????????????? ?????????????????? ??????????: ??????, ???????????????? ?? ??????????????.
    """
    serializer_class = EditManagerProfileSerializer

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.EditManagerProfileView().patch(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


# SECURITY
class CreateSecurityByAdmin(BaseAPIView):
    """
    ???????????????? ?????????????????? ?????????? ??????????.???????????? ????????????????????????????.
    ?????????? ?? ???????????? ?????? ?????????????? ?????????? ?????????????????? ???????????????? ?? ?????????? ???? ????????????.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.CreateSecurityByAdmin().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AuthenticateSecurity(BaseAPIView):
    """
        ???????? ???????????? ?? ???????????? ???? ????????????????????
    """
    permission_classes = []
    serializer_class = UsernameWithPasswordSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.AuthenticateSecurity().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


####

class UsersRating(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.UsersRating().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyRating(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyRating().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class UserCareer(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.UserCareer().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfileCards(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCards().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileCards().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class MyProfileInsurance(APIView):
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.MyProfileInsurance().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class ConfirmInsurance(APIView):
    @staticmethod
    def post(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.ConfirmInsurance().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminAuth(APIView):
    permission_classes = (AllowAny,)


    @staticmethod
    def post(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.AdminAuth().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminProfile(APIView):
    permission_classes = [IsAdminOrManager]
    @staticmethod
    def get(request, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.AdminProfile().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminProfilePassword(APIView):
    permission_classes = [IsAdminOrManager]

    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        if request.version in ['users_1_0']:
            return v1_0.AdminProfilePassword().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)


class AdminUploads(APIView):
    permission_classes = [IsAdminOrManager]
    @staticmethod
    def post(request):
        if request.version in ['users_1_0']:
            return v1_0.AdminUploads().post(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)

    @staticmethod
    def delete(request):
        if request.version in ['users_1_0']:
            return v1_0.AdminUploads().delete(request)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND)