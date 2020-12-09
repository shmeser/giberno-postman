from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from app_users.controllers import FirebaseController
from app_users.entities import TokenEntity
from app_users.mappers import TokensMapper
from app_users.models import JwtToken
from app_users.versions.v1_0.repositories import AuthRepository, JwtRepository, UsersRepository
from app_users.versions.v1_0.serializers import RefreshTokenSerializer
from backend.errors.http_exception import HttpException
from backend.utils import get_request_headers, timestamp_to_datetime, get_request_body


@api_view(['GET'])
@permission_classes([AllowAny])
def firebase_web_auth(request):
    return render(request, 'app_users/v1_0/index.html')


@login_required
def social_web_auth(request):
    return render(request, 'app_users/v1_0/home.html', context={'user': request.user})


def login(request):
    return render(request, 'app_users/v1_0/login.html')


class AuthFirebase(APIView):
    @classmethod
    def post(cls, request):
        headers = get_request_headers(request)
        body = get_request_body(request)
        firebase_token: TokenEntity = TokensMapper.firebase(body)
        decoded_token = FirebaseController.verify_token(firebase_token.token)

        user, created = AuthRepository.get_or_create_social_user(
            uid=decoded_token.get('uid'),
            social_type=decoded_token.get('firebase').get('sign_in_provider'),
            access_token=firebase_token.token,
            access_token_expiration=timestamp_to_datetime(decoded_token.get('exp', None), milliseconds=False)
            if decoded_token.get('exp', None) is not None else None,
            phone=decoded_token.get('phone_number', None),
            email=decoded_token.get('email', None),
            # account_type=body.get('account_type', AccountType.SELF_EMPLOYED),
            reference_code=body.get('reference_code', None),
            **decoded_token.get('firebase', None)
        )

        # if request.user and not request.user.is_anonymous:  # Если отсылался заголовок Authorization
        #     """ Если запрос пришел от соц юзера, и привязывается к другому соц юзеру, отдаем ошибку"""
        #     raise HttpException(detail='Нельзя привязать соцсеть к аккаунту с соцсетью',
        #                         status_code=status.HTTP_403_FORBIDDEN)

        JwtRepository().remove_old(user)  # TODO пригодится для запрета входа с нескольких устройств
        jwt_pair: JwtToken = JwtRepository(headers).create_jwt_pair(user)

        return JsonResponse({
            'accessToken': jwt_pair.access_token,
            'refreshToken': jwt_pair.refresh_token
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
                raise HttpException(detail="JWT-токен не найден, обновление невозможно",
                                    status_code=status.HTTP_401_UNAUTHORIZED)

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
            raise HttpException(detail='Невалидный реферальный код', status_code=status.HTTP_400_BAD_REQUEST)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def get(request):
        return JsonResponse({
            "referenceCode": format(request.user.uuid.fields[5], 'x')
        })
