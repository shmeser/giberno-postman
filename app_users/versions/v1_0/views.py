from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from social_core.exceptions import AuthTokenRevoked
from social_django.utils import load_backend, load_strategy

from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.controllers import FirebaseController
from app_users.entities import TokenEntity, SocialEntity
from app_users.enums import NotificationType
from app_users.mappers import TokensMapper, SocialDataMapper
from app_users.models import JwtToken
from app_users.versions.v1_0.repositories import AuthRepository, JwtRepository, UsersRepository, ProfileRepository, \
    SocialsRepository, NotificationsRepository, CareerRepository, DocumentsRepository
from app_users.versions.v1_0.serializers import RefreshTokenSerializer, ProfileSerializer, SocialSerializer, \
    NotificationsSettingsSerializer, NotificationSerializer, CareerSerializer, DocumentSerializer
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
            base_user=request.user or None
        )

        # Проверка реферального кода
        reference_code = body.get('reference_code', None)
        if reference_code:
            reference_user = UsersRepository.get_reference_user(reference_code)
            if reference_user is None:
                raise HttpException(detail='Невалидный реферальный код', status_code=RESTErrors.BAD_REQUEST)

            user.reg_reference = reference_user
            user.reg_reference_code = reference_code
            user.save()

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

    def patch(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(request.user, data=body)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class MyProfileUploads(APIView):
    def post(self, request):
        uploaded_files = RequestMapper.file_entities(request, request.user)
        saved_files = MediaRepository().bulk_create(uploaded_files)
        serializer = MediaSerializer(saved_files, many=True)
        return Response(camelize(serializer.data), status=status.HTTP_200_OK)

    def delete(self, request):
        body = get_request_body(request)
        uuid_list = body.get('uuid', [])
        uuid_list = uuid_list if isinstance(uuid_list, list) else [uuid_list]
        if uuid_list:
            MediaRepository().filter_by_kwargs({
                'owner_id': request.user.id,
                'owner_ct_id': ContentType.objects.get_for_model(request.user).id,
                'uuid__in': uuid_list
            }).update(**{
                'deleted': True,
                'updated_at': now()
            })
        return Response(None, status=status.HTTP_204_NO_CONTENT)


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


class MyProfileSocials(APIView):
    def get(self, request):
        serializer = SocialSerializer(
            request.user.socialmodel_set.filter(deleted=False).order_by('-created_at'),
            many=True
        )
        return Response(camelize(serializer.data), status=status.HTTP_200_OK)

    def delete(self, request):
        body = get_request_body(request)
        id_list = body.get('id', [])
        id_list = id_list if isinstance(id_list, list) else [id_list]
        if id_list:
            if SocialsRepository().filter_by_kwargs({
                'user': request.user,
                'id__in': id_list,
                'is_for_reg': True  # Проверяем, есть ли среди соцсетей та, через которую был создан аккаунт
            }).exists():
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.DELETING_REG_SOCIAL))
                ])

            SocialsRepository().filter_by_kwargs({
                'user': request.user,
                'id__in': id_list,
            })
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class Notifications(CRUDAPIView):
    serializer_class = NotificationSerializer
    repository_class = NotificationsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'title': 'title__istartswith',
        'message': 'message__istartswith',
    }

    default_order_params = ['-created_at']

    default_filters = {
        'deleted': False
    }

    order_params = {
        'created': 'created_at',
    }

    def __init__(self):
        super().__init__()
        self.serializer_class = NotificationSerializer

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(request, self.filter_params, self.date_filter_params,
                                          self.default_filters) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            serialized = self.serializer_class(dataset, many=True)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class NotificationsSettings(APIView):
    def get(self, request):
        serializer = NotificationsSettingsSerializer(
            request.user.notificationssettings,
            many=False
        )
        return Response(camelize(serializer.data), status=status.HTTP_200_OK)

    def put(self, request):
        body = get_request_body(request)
        types_list = body.get('enabled_types', [])
        types_list = types_list if isinstance(types_list, list) else [types_list]
        types_list = list(filter(lambda x: NotificationType.has_value(x), types_list))  # Фильтруем ненужные значения

        request.user.notificationssettings.enabled_types = types_list
        request.user.notificationssettings.save()

        serializer = NotificationsSettingsSerializer(
            request.user.notificationssettings,
            many=False
        )

        return Response(camelize(serializer.data), status=status.HTTP_200_OK)


class MyProfileCareer(CRUDAPIView):
    serializer_class = CareerSerializer
    repository_class = CareerRepository

    allowed_http_methods = ['get', 'post', 'patch', 'delete']

    filter_params = {
    }

    default_order_params = ['year_start']

    default_filters = {
    }

    order_params = {
    }

    def __init__(self):
        super().__init__()
        self.serializer_class = CareerSerializer

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(request, self.filter_params, self.date_filter_params,
                                          self.default_filters) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
        serialized = self.serializer_class(dataset, many=self.many)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(data=body)
        serialized.is_valid(raise_exception=True)
        serialized.save()

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request)
        body['user_id'] = request.user.id

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset, data=body)
            serialized.is_valid(raise_exception=True)
            serialized.save()
        else:
            raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        if record_id:
            record = self.repository_class().filter_by_kwargs(
                {'id': record_id, 'deleted': False, 'user_id': request.user.id}
            ).first()
            if record:
                record.deleted = True
                record.save()
        else:
            raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class MyProfileDocuments(CRUDAPIView):
    serializer_class = DocumentSerializer
    repository_class = DocumentsRepository

    allowed_http_methods = ['get', 'post', 'patch', 'delete']

    filter_params = {
    }

    default_order_params = ['-created_at']

    default_filters = {
    }

    order_params = {
    }

    def __init__(self):
        super().__init__()
        self.serializer_class = DocumentSerializer

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(request, self.filter_params, self.date_filter_params,
                                          self.default_filters) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
        serialized = self.serializer_class(dataset, many=self.many)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request):
        body = get_request_body(request)
        body['user_id'] = request.user.id

        serialized = self.serializer_class(data=body)
        serialized.is_valid(raise_exception=True)

        document = serialized.save()
        self.repository_class().update_media(document, body.pop('attach_files', None))
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request)
        body['user_id'] = request.user.id

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset, data=body)
            serialized.is_valid(raise_exception=True)
            document = serialized.save()
            self.repository_class().update_media(document, body.pop('attach_files', None))
        else:
            raise HttpException(detail='Не указан ID', status_code=RESTErrors.BAD_REQUEST)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        if record_id:
            record = self.repository_class().filter_by_kwargs(
                {'id': record_id, 'deleted': False, 'user_id': request.user.id}
            ).first()
            if record:
                record.deleted = True
                record.save()
        else:
            raise HttpException(detail='Не указан ID', status_code=RESTErrors.BAD_REQUEST)

        return Response(None, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def read_notification(request, **kwargs):
    NotificationsRepository().filter_by_kwargs({
        'id': kwargs.get('record_id'),
        'read_at__isnull': True
    }).update(
        read_at=now(),
        updated_at=now(),
    )

    return Response(None, status=status.HTTP_204_NO_CONTENT)
