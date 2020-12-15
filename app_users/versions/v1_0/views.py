from django.http import JsonResponse
from django.shortcuts import render
from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from social_core.exceptions import AuthTokenRevoked
from social_django.utils import load_backend, load_strategy

from app_users.controllers import FirebaseController
from app_users.entities import TokenEntity, SocialEntity
from app_users.mappers import TokensMapper, SocialDataMapper
from app_users.models import JwtToken
from app_users.versions.v1_0.repositories import AuthRepository, JwtRepository, UsersRepository, ProfileRepository
from app_users.versions.v1_0.serializers import RefreshTokenSerializer, ProfileSerializer, FillProfileSerializer
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException, CustomException
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers, get_request_body


@api_view(['GET'])
@permission_classes([AllowAny])
def firebase_web_auth(request):
    return render(request, 'app_users/index.html')


class AuthFirebase(APIView):
    @classmethod
    def post(cls, request):
        headers = get_request_headers(request)
        body = get_request_body(request)

        firebase_token: TokenEntity = TokensMapper.firebase(body)
        decoded_token = FirebaseController.verify_token(firebase_token.token)

        social_data: SocialEntity = SocialDataMapper.firebase(decoded_token)
        social_data.access_token = firebase_token.token

        user, created = AuthRepository.get_or_create_social_user(
            social_data,
            # account_type=body.get('account_type', AccountType.SELF_EMPLOYED),
            reference_code=body.get('reference_code', None)
        )

        # if request.user and not request.user.is_anonymous:  # Если отсылался заголовок Authorization
        #     """ Если запрос пришел от соц юзера, и привязывается к другому соц юзеру, отдаем ошибку"""
        #     raise HttpException(detail='Нельзя привязать соцсеть к аккаунту с соцсетью',
        #                         status_code=RESTErrors.FORBIDDEN)

        JwtRepository().remove_old(user)  # TODO пригодится для запрета входа с нескольких устройств
        jwt_pair: JwtToken = JwtRepository(headers).create_jwt_pair(user)

        return JsonResponse({
            'accessToken': jwt_pair.access_token,
            'refreshToken': jwt_pair.refresh_token
        })


class AuthVk(APIView):
    def __init__(self, request, *args, **kwargs):
        super().__init__()
        self.headers = get_request_headers(request)

    def post(self, request):
        body = get_request_body(request)
        vk_token: TokenEntity = TokensMapper.vk(body)
        backend = load_backend(load_strategy(request), 'vk-oauth2', 'social/login')
        try:
            social_user = backend.do_auth(access_token=vk_token.token, user=request.user or None, **{
                'reference_code': body.get('reference_code', None)
            })
        except AuthTokenRevoked as e:
            raise HttpException(detail=str(e), status_code=RESTErrors.NOT_AUTHORIZED)

        if social_user and request.user:
            """ Привязали соцсеть, получаем jwt для текущего пользователя """
            user = request.user
        elif social_user and not request.user:
            """ Регистрация нового пользователя через соцсеть """
            user = social_user
        else:
            raise HttpException(detail='Ошибка входа через соцсеть', status_code=RESTErrors.NOT_AUTHORIZED)

        JwtRepository().remove_old(user)  # TODO пригодится для запрета входа с нескольких устройств
        jwt_pair: JwtToken = JwtRepository().create_jwt_pair(user)

        return JsonResponse({
            'accessToken': jwt_pair.access_token,
            'refreshToken': jwt_pair.refresh_token,
        })


class AuthRefreshToken(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        body = get_request_body(request)
        serializer = RefreshTokenSerializer(data=body)

        try:
            serializer.is_valid(raise_exception=True)
            jwt_pair = JwtRepository().refresh(
                serializer.initial_data.get('refresh_token'),
                serializer.validated_data.get('access_token')
            )
            if jwt_pair is None:
                raise HttpException(
                    detail="JWT-токен не найден, обновление невозможно",
                    status_code=RESTErrors.NOT_AUTHORIZED
                )

        except TokenError as e:
            raise InvalidToken(e.args[0])

        return JsonResponse({
            'accessToken': jwt_pair.access_token,
            'refreshToken': jwt_pair.refresh_token,
        })


class ReferenceCode(APIView):

    @staticmethod
    def post(request):
        body = get_request_body(request)
        reference_user = UsersRepository.get_reference_user(body.get('reference_code', None))
        if reference_user is None:
            raise HttpException(detail='Невалидный реферальный код', status_code=RESTErrors.BAD_REQUEST)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get(request):
        return JsonResponse({
            "referenceCode": format(request.user.uuid.fields[5], 'x')
        })


class MyProfile(CRUDAPIView):
    serializer_class = ProfileSerializer
    repository_class = ProfileRepository
    allowed_http_methods = ['get']

    def __init__(self):
        super().__init__()
        self.serializer_class = ProfileSerializer

    def get(self, request, **kwargs):
        serialized = self.serializer_class(request.user, many=False)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def put(self, request, **kwargs):
        body = get_request_body(request)
        serialized = FillProfileSerializer(request.user, data=body)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(request.user, data=body)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Users(CRUDAPIView):
    serializer_class = ProfileSerializer
    repository_class = ProfileRepository
    allowed_http_methods = ['get']

    filter_params = {
        'username': 'username__istartswith',
    }

    default_order_params = []

    default_filters = {
        'is_staff': False
    }

    order_params = {
        'username': 'username',
    }

    def __init__(self):
        super().__init__()
        self.serializer_class = ProfileSerializer

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(request, self.filter_params, self.date_filter_params,
                                          self.default_filters) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            self.serializer_class = ProfileSerializer

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            serialized = self.serializer_class(dataset, many=True)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)
