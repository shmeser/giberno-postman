import json
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from social_core.exceptions import AuthTokenRevoked
from social_django.utils import load_backend, load_strategy

from app_chats.versions.v1_0.repositories import ChatsRepository
from app_games.enums import TaskKind
from app_market.versions.v1_0.repositories import ShiftAppealsRepository, InsuranceRepository
from app_market.versions.v1_0.serializers import InsuranceSerializer
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_sockets.controllers import SocketController
from app_sockets.enums import AvailableVersion
from app_users.controllers import FirebaseController
from app_users.entities import TokenEntity, SocialEntity
from app_users.enums import NotificationType, AccountType
from app_users.mappers import TokensMapper, SocialDataMapper
from app_users.models import JwtToken
from app_users.versions.v1_0.repositories import AuthRepository, JwtRepository, UsersRepository, ProfileRepository, \
    SocialsRepository, NotificationsRepository, CareerRepository, DocumentsRepository, FCMDeviceRepository, \
    RatingRepository, CardsRepository
from app_users.versions.v1_0.serializers import RefreshTokenSerializer, ProfileSerializer, SocialSerializer, \
    NotificationsSettingsSerializer, NotificationSerializer, CareerSerializer, DocumentSerializer, \
    CreateManagerByAdminSerializer, UsernameSerializer, UsernameWithPasswordSerializer, \
    PasswordSerializer, EditManagerProfileSerializer, CreateSecurityByAdminSerializer, RatingSerializer, CardsSerializer
from backend.api_views import BaseAPIView
from backend.entity import Error
from backend.enums import Platform
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException, CustomException
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers, get_request_body, chained_get
from app_games.tasks import check_everyday_tasks_for_user


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

    def get(self, request, **kwargs):
        serialized = self.serializer_class(request.user, many=False, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        check_everyday_tasks_for_user.s(user_id=request.user.id, kind=TaskKind.OPEN_APP.value).apply_async()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(request.user, data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class MyProfileUploads(APIView):
    def post(self, request):
        uploaded_files = RequestMapper.file_entities(request, request.user)
        saved_files = MediaRepository(request.user).bulk_create(uploaded_files)
        serializer = MediaSerializer(saved_files, many=True, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serializer.data), status=status.HTTP_200_OK)

    def delete(self, request):
        body = get_request_body(request)
        uuid_list = body.get('uuid', [])
        uuid_list = uuid_list if isinstance(uuid_list, list) else [uuid_list]
        if uuid_list:
            doc_ct_id, my_docs_ids = DocumentsRepository(me=request.user).get_my_docs_ids()
            MediaRepository(request.user).delete_my_media(uuid_list, doc_ct_id, my_docs_ids)
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
        'is_staff': False,
        'account_type': AccountType.SELF_EMPLOYED.value
    }

    order_params = {
        'username': 'username',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class MyProfileSocials(APIView):
    def get(self, request):
        serializer = SocialSerializer(
            request.user.socialmodel_set.filter(deleted=False).order_by('-created_at'),
            many=True,
            context={
                'me': request.user,
                'headers': get_request_headers(request),
            }
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

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs={**filters, **{'user': request.user}}, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
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
        sound_enabled = body.get('sound_enabled', None)
        types_list = types_list if isinstance(types_list, list) else [types_list]
        types_list = list(filter(lambda x: NotificationType.has_value(x), types_list))  # Фильтруем ненужные значения

        request.user.notificationssettings.enabled_types = types_list
        if sound_enabled is not None:
            request.user.notificationssettings.sound_enabled = sound_enabled in [
                'true', 'TRUE', True
            ]

        request.user.notificationssettings.save()

        serializer = NotificationsSettingsSerializer(
            request.user.notificationssettings,
            many=False, context={
                'me': request.user,
                'headers': get_request_headers(request),
            }
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

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class().filter_by_kwargs(
                kwargs={**filters, **{
                    'user': request.user
                }}, paginator=pagination, order_by=order_params
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request)
        body['user_id'] = request.user.id

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset, data=body, context={
                'me': request.user,
                'headers': get_request_headers(request),
            })
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

    allowed_http_methods = ['get', 'post']

    array_filter_params = {
        'type': 'type__in'
    }

    default_order_params = ['-created_at']

    default_filters = {
    }

    order_params = {
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class(me=request.user).inited_get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(me=request.user).inited_filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request):
        body = get_request_body(request)
        body['user_id'] = request.user.id

        serialized = self.serializer_class(data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)

        document = serialized.save()
        self.repository_class.update_media(document, body.pop('attach_files', None), request.user)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class MyProfileDocument(MyProfileDocuments):
    allowed_http_methods = ['get', 'patch', 'delete']

    def patch(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request)
        body['user_id'] = request.user.id

        if record_id:
            dataset = self.repository_class(me=request.user).inited_get_by_id(record_id)
            serialized = self.serializer_class(dataset, data=body, context={
                'me': request.user,
                'headers': get_request_headers(request),
            })
            serialized.is_valid(raise_exception=True)
            document = serialized.save()
            self.repository_class.update_media(document, body.pop('attach_files', None), request.user)
        else:
            raise HttpException(detail='Не указан ID', status_code=RESTErrors.BAD_REQUEST)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        if record_id:
            record = self.repository_class(me=request.user).inited_get_by_id(record_id)
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

    indicators_dict = {
        'newNotifications': NotificationsRepository(me=request.user).get_unread_notifications_count(),
        'chatsUnreadMessages': ChatsRepository(me=request.user).get_all_chats_unread_count()
    }
    if request.user.account_type == AccountType.SELF_EMPLOYED.value:
        indicators_dict['newConfirmedAppeals'] = ShiftAppealsRepository(
            me=request.user).get_new_confirmed_count()

    if request.user.account_type == AccountType.MANAGER.value:
        indicators_dict['newAppeals'] = ShiftAppealsRepository(
            me=request.user).get_new_appeals_count()

    SocketController(me=request.user, version=AvailableVersion.V1_0.value).send_message_to_my_connections({
        'type': 'counters_for_indicators',
        'prepared_data': indicators_dict,
    })

    return Response(None, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def push_subscribe(request):
    request = request._request
    data = get_request_body(request)
    headers = get_request_headers(request)

    token = chained_get(data, 'token')
    platform = chained_get(headers, 'Platform')

    if platform:
        platform = platform.lower()
        platform = Platform.ANDROID.value if Platform.ANDROID.value in platform else platform
        platform = Platform.IOS.value if Platform.IOS.value in platform else platform

    if not token:
        raise CustomException(errors=[
            dict(Error(ErrorsCodes.EMPTY_REQUIRED_FIELDS, **{'detail': 'Необходимо указать поле token'}))
        ])

    if platform is None:
        raise CustomException(errors=[
            dict(
                Error(
                    ErrorsCodes.EMPTY_REQUIRED_FIELDS,
                    **{'detail': 'Необходимо указать заголовок запроса Platform'}
                )
            )
        ])

    data["type"] = platform
    data["registration_id"] = token
    body = json.dumps(data).encode('utf-8')
    request._body = body
    FCMDeviceAuthorizedViewSet.as_view({'post': 'create'})(request)
    return Response(None, status=status.HTTP_204_NO_CONTENT)


class PushUnsubscribe(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        data = get_request_body(request)
        FCMDeviceRepository().filter_by_kwargs({
            'registration_id': data.get('token')
        }).update(active=False)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


# MANAGERS RELATED VIEWS
class CreateManagerByAdminAPIView(BaseAPIView):
    serializer_class = CreateManagerByAdminSerializer
    repository_class = ProfileRepository

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            user = self.repository_class(me=request.user).create_manager_by_admin(serializer.validated_data)
            return Response(camelize(ProfileSerializer(instance=user).data))


class GetManagerByUsernameAPIView(BaseAPIView):
    permission_classes = []
    serializer_class = UsernameSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            ProfileRepository().get_by_username(username=serializer.validated_data['username'])
            return Response(status=status.HTTP_200_OK)


class AuthenticateManagerAPIView(BaseAPIView):
    permission_classes = []
    serializer_class = UsernameWithPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            user = ProfileRepository().get_by_username_and_password(validated_data=serializer.validated_data)
            JwtRepository.remove_old(user)
            headers = get_request_headers(request)
            jwt_pair: JwtToken = JwtRepository(headers).create_jwt_pair(user)
            response_data = {
                'accessToken': jwt_pair.access_token,
                'refreshToken': jwt_pair.refresh_token,
                'password_changed': user.password_changed
            }
            return Response(response_data)


class ChangeManagerPasswordAPIView(BaseAPIView):
    serializer_class = PasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            request.user.set_password(raw_password=serializer.validated_data['password'])
            request.user.password_changed = True
            request.user.save()
            return Response(status=status.HTTP_200_OK)


class EditManagerProfileView(BaseAPIView):
    serializer_class = EditManagerProfileSerializer

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            username = serializer.validated_data.get('username')
            if username:
                ProfileRepository(me=request.user).update_username(username)
                del serializer.validated_data['username']

            user = ProfileRepository().update(record_id=request.user.id, **serializer.validated_data)
            return Response(camelize(ProfileSerializer(instance=user).data))


# SECURITY
class CreateSecurityByAdmin(BaseAPIView):
    serializer_class = CreateSecurityByAdminSerializer
    repository_class = ProfileRepository

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            username, password = self.repository_class(
                me=request.user
            ).create_security_by_admin(serializer.validated_data)
            return Response(camelize({
                'username': username,
                'password': password
            }))


class AuthenticateSecurity(BaseAPIView):
    permission_classes = []
    serializer_class = UsernameWithPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            user = ProfileRepository().get_by_username_and_password(validated_data=serializer.validated_data)
            headers = get_request_headers(request)
            jwt_pair: JwtToken = JwtRepository(headers).create_jwt_pair(
                user,
                lifetime=timedelta(days=3650)  # Token на 10 лет
            )

            response_data = {
                'accessToken': jwt_pair.access_token,
                'refreshToken': jwt_pair.refresh_token,
            }
            return Response(response_data)


class UsersRating(CRUDAPIView):
    serializer_class = RatingSerializer
    repository_class = RatingRepository

    allowed_http_methods = ['get']

    filter_params = {
        'region': 'reviews__region_id'
    }

    date_filter_params = {
        'date_from': 'reviews__created_at__gte',
        'date_to': 'reviews__created_at__lte'
    }

    array_filter_params = {
    }

    default_filters = {}

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)

        self.many = True
        dataset = self.repository_class(me=request.user).get_users_rating(
            kwargs=filters, paginator=pagination
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class MyRating(CRUDAPIView):
    serializer_class = RatingSerializer
    repository_class = RatingRepository

    allowed_http_methods = ['get']

    filter_params = {
        'region': 'reviews__region_id'
    }

    date_filter_params = {
        'date_from': 'reviews__created_at__gte',
        'date_to': 'reviews__created_at__lte'
    }

    array_filter_params = {
    }

    default_filters = {}

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()

        self.many = False
        dataset = self.repository_class(me=request.user).get_my_rating(
            kwargs=filters
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class UserCareer(CRUDAPIView):
    serializer_class = CareerSerializer
    repository_class = CareerRepository

    allowed_http_methods = ['get']

    filter_params = {
    }

    default_order_params = ['year_start']

    default_filters = {
    }

    order_params = {
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        self.many = True
        dataset = self.repository_class().filter_by_kwargs(
            kwargs={**filters, **{
                'user_id': record_id
            }}, paginator=pagination, order_by=order_params
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class MyProfileCards(CRUDAPIView):
    serializer_class = CardsSerializer
    repository_class = CardsRepository

    allowed_http_methods = ['get', 'delete']

    default_order_params = ['-created_at']

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class(me=request.user).inited_get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(me=request.user).get_my_cards(paginator=pagination, order_by=order_params)

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        if record_id:
            record = self.repository_class(me=request.user).inited_get_by_id(record_id)
            record.deleted = True
            record.save()
        else:
            raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class MyProfileInsurance(CRUDAPIView):
    serializer_class = InsuranceSerializer
    repository_class = InsuranceRepository

    allowed_http_methods = ['get', ]

    default_order_params = ['-created_at']

    def get(self, request, **kwargs):
        dataset = self.repository_class(me=request.user).get_nearest_active_insurance()
        self.many = False
        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class ConfirmInsurance(CRUDAPIView):
    serializer_class = InsuranceSerializer
    repository_class = InsuranceRepository

    allowed_http_methods = ['post']

    def post(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        if record_id:
            record = self.repository_class(me=request.user).inited_get_by_id(record_id)
            record.confirmed_at = now()
            record.save()
        else:
            raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)

        serialized = self.serializer_class(record, many=False, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class AdminPanelAuth(APIView):
    permission_classes = []
    serializer_class = UsernameWithPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            user = ProfileRepository().get_by_username_and_password(validated_data=serializer.validated_data)
            headers = get_request_headers(request)
            JwtRepository.remove_old(user)
            jwt_pair: JwtToken = JwtRepository(headers).create_jwt_pair(
                user,
                lifetime=timedelta(days=3650)  # Token на 10 лет
            )

            role = 'selfEmployed'
            if user.account_type == AccountType.ADMIN:
                if user.is_superuser:
                    role = 'superadmin'
                else:
                    role = 'admin'
            if user.account_type == AccountType.MANAGER:
                role = 'manager'
            if user.account_type == AccountType.SECURITY:
                role = 'security'

            response_data = {
                'accessToken': jwt_pair.access_token,
                'refreshToken': jwt_pair.refresh_token,
                'role': role
            }
            return Response(response_data)


class AdminPanelProfile(APIView):
    def get(self, request, *args, **kwargs):

        role = 'selfEmployed'
        if request.user.account_type == AccountType.ADMIN:
            if request.user.is_superuser:
                role = 'superadmin'
            else:
                role = 'admin'
        if request.user.account_type == AccountType.MANAGER:
            role = 'manager'
        if request.user.account_type == AccountType.SECURITY:
            role = 'security'

        response_data = {
            'id': request.user.id,
            'role': role,
            'username': request.user.username,
            'first_name': request.user.first_name,
            'middle_name': request.user.middle_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': request.user.phone
        }
        return Response(camelize(response_data))
