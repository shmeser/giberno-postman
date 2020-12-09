from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from app_users.controllers import FirebaseController
from app_users.entities import TokenEntity
from app_users.enums import AccountType
from app_users.mappers import TokensMapper
from app_users.models import JwtToken
from app_users.versions.v1_0.repositories import AuthRepository, JwtRepository
from app_users.versions.v1_0.serializers import RefreshTokenSerializer
from backend.errors.http_exception import HttpException
from backend.utils import get_request_headers, timestamp_to_datetime, get_request_body


# from backend.errors.enums import RESTErrors
# from backend.errors.http_exception import HttpException
# from backend.utils import get_body_in_request, milliseconds_to_datetime
# from media.mappers import RequestToMediaEntity
# from media.repositories import MediaRepository
# from subscriptions.tasks import check_subscription
# from users.enums import GenderEnum
# from users.permissions import FilledProfilePermission
# from users.repositories import UsersRepository
# from users.serializers import UserSerializer, UserPatchSerializer
# class User(APIView):
#     permission_classes = (IsAuthenticated,)
#     serializer_class = UserSerializer
#     nullable_fields = {
#         'birth_date',
#         'phone_number',
#         'avatar',
#         'sex',
#         'height',
#         'weight',
#         'daily_calorie_intake',
#         'city',
#         'religion',
#         'vegetarianism',
#         'invited_by',
#         'email'
#     }
#
#     def get(self, request):
#         FilledProfilePermission().has_permission(request)
#         check_subscription(request.user.id)
#         user_data = self.serializer_class(request.user)
#         return Response(camelize(user_data.data), status=status.HTTP_200_OK)
#
#     def put(self, request):
#         data = get_body_in_request(request)
#
#         {data.setdefault(nullable_field) for nullable_field in self.nullable_fields}
#
#         user_data = self.serializer_class(request.user, data=data)
#         user_data.is_valid(raise_exception=True)
#         user_data.save()
#         return Response(camelize(user_data.data), status=status.HTTP_200_OK)
#
#     def patch(self, request):
#         data = get_body_in_request(request)
#
#         serializer = UserPatchSerializer(request.user, data=data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(camelize(serializer.data), status=status.HTTP_200_OK)
#
#     def delete(self, request):
#         UsersRepository().delete_profile(request.user)
#         return JsonResponse({'status': 200})
#
#     @staticmethod
#     @swagger_auto_schema(
#         responses={
#             status.HTTP_200_OK: UserSerializer,
#             Errors.MESSAGE_TYPE_ERROR.value: Errors.MESSAGE_TYPE_ERROR.name,
#             Errors.BAD_REQUEST.value: Errors.BAD_REQUEST.name,
#             Errors.UUID_UNIQUE_ERROR.value: Errors.UUID_UNIQUE_ERROR.name
#         },
#         method='PATCH',
#         tags=['User']
#     )
#     @api_view(['PATCH'])
#     def upload_avatar(request, **kwargs):
#         media_entity = RequestToMediaEntity.map(request)
#         media = MediaRepository.create_media(media_entity)
#
#         user = UsersRepository().update(request.user.id, avatar=media)
#         user_data = UserSerializer(user)
#
#         return Response(camelize(user_data.data), status=status.HTTP_200_OK)
#
#
# @swagger_auto_schema(responses={status.HTTP_200_OK: 'daily_calories_intake'}, method='GET', tags=['User'])
# @api_view(['GET'])
# @permission_classes([AllowAny])
# def calculate_calories(request, **kwargs):
#     serializer = UserSerializer()
#     REQUIRED_FIELDS = ['height', 'weight']
#     fields = underscoreize(request.query_params.copy())
#
#     data = {i: float(fields.get(i)) for i in REQUIRED_FIELDS}
#     birth_date_ts_str = fields.get('birth_date', None)
#
#     serializer.validate_weight(data.get('weight'))
#     serializer.validate_height(data.get('height'))
#
#     if all([True if i in fields else False for i in REQUIRED_FIELDS]):
#         try:
#             sex = int(fields.get('sex', GenderEnum.MALE.value))
#         except ValueError as e:
#             raise HttpException(status_code=Errors.BAD_REQUEST.value, detail=e)
#         if not birth_date_ts_str or birth_date_ts_str.lower() == 'null':  # Если пустая строка, null или None
#             data['birth_date'] = None
#         else:
#             data['birth_date'] = milliseconds_to_datetime(int(float(birth_date_ts_str)))
#         calories = UsersRepository().calculate_calories(sex, data)
#         return Response(camelize({'daily_calories_intake': calories}), status=status.HTTP_200_OK)
#     return Response(camelize({'daily_calories_intake': 0}), status=status.HTTP_200_OK)


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
        """
        1)  Если пришел неавторизованный запрос, создаем пользователя, генерируем ему uuid, привязываем ему соц сеть
        2)  Если авториз. запрос от анонимного юзера, создаем нового пользователя (если такогового нет еще),
            привязываем ему соцсеть, переносим всю статистику анонимного пользователя новому пользователю с соцсетью,
            удаляем jwt анона и всю его статистику
        3)  Если авторизованный запрос от анонимного юзера, а при попытке создания нового соц юзера уже таковой есть,
            то отдаем этого пользователя без переноса статистики
        4)  Если авторизованный запрос от юзера с соцсетью, и привязывается к другому соц юзеру, то выдаем ошибку
        """

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
            account_type=body.get('account_type', AccountType.SELF_EMPLOYED),
            reference_code=body.get('reference_code', None),
            **decoded_token.get('firebase', None)
        )

        if request.user and not request.user.is_anonymous:  # Если отсылался заголовок Authorization
            """ Если запрос пришел от соц юзера, и привязывается к другому соц юзеру, отдаем ошибку"""
            if request.user.uid is not None and user.id != request.user.id:
                raise HttpException(detail='Нельзя привязать соцсеть к аккаунту с соцсетью',
                                    status_code=status.HTTP_403_FORBIDDEN)

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
