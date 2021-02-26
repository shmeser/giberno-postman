from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.timezone import now
from fcm_django.models import FCMDevice
from rest_framework_simplejwt.tokens import RefreshToken

from app_media.versions.v1_0.repositories import MediaRepository
from app_users.entities import JwtTokenEntity, SocialEntity
from app_users.enums import AccountType, NotificationType
from app_users.models import SocialModel, UserProfile, JwtToken, NotificationsSettings, Notification, UserCareer, \
    Document
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.http_exception import HttpException, CustomException
from backend.mixins import MasterRepository
from backend.repositories import BaseRepository
from backend.utils import is_valid_uuid


class UsersRepository:
    @staticmethod
    def get_reference_user(reference_code):
        return UserProfile.objects.filter(uuid__icontains=reference_code, deleted=False).first()


class AuthRepository:

    @staticmethod
    def social_registration(social, social_data, defaults, account_type):
        user, created = UserProfile.objects.get_or_create(socialmodel=social, defaults=defaults)

        if created:
            # Привязываем пользователя к соцсети
            social.user = user
            social.is_for_reg = True
            social.save()
            user.email = social_data.email

            # Создаем модель настроек для уведомлений
            NotificationsSettings.objects.create(
                user=user,
                enabled_types=[NotificationType.SYSTEM]
            )
        else:
            # Если ранее уже создан аккаунт и при регистрации указан другой тип аккаунта
            if user.account_type != account_type:
                raise HttpException(
                    detail=ErrorsCodes.ALREADY_REGISTERED_WITH_OTHER_ROLE.value,
                    status_code=RESTErrors.FORBIDDEN
                )

            # Подставляем имеил с соцсети, если его нет
            user.email = social_data.email if not user.email and social_data.email else user.email
            # Подставляем телефон из соцсети всегда
            user.phone = social_data.phone if social_data.phone else user.phone

        user.save()

        return user, created

    @staticmethod
    def social_attaching(social, social_data, base_user):
        user = UserProfile.objects.filter(socialmodel=social).first()

        if user is not None:
            # Пользователь для соцсети найден

            if user.id != base_user.id:
                raise HttpException(
                    detail=ErrorsCodes.SOCIAL_ALREADY_IN_USE.value,
                    status_code=RESTErrors.FORBIDDEN
                )
            # Найден свой аккаунт
            # Подставляем имеил с соцсети, если его нет
            user.email = social_data.email if not user.email and social_data.email else user.email
            # Подставляем телефон из соцсети всегда
            user.phone = social_data.phone if social_data.phone else user.phone

            user.save()

            result = user

        else:
            # Пользователь для соцсети не найден

            # Привязываем ооцсеть к своему base_user
            social.user = base_user
            social.save()

            # Подставляем имеил с соцсети, если его нет
            base_user.email = social_data.email if not base_user.email and social_data.email else base_user.email
            # Подставляем телефон из соцсети всегда
            base_user.phone = social_data.phone if social_data.phone else base_user.phone

            base_user.save()

            result = base_user

        return result

    @classmethod
    def get_or_create_social_user(cls, social_data: SocialEntity, account_type=AccountType.SELF_EMPLOYED,
                                  base_user: UserProfile = None):

        # Получаем способ авторизации
        social, social_created = SocialModel.objects.get_or_create(
            social_id=social_data.social_id, type=social_data.social_type, defaults=social_data.get_kwargs()
        )

        # Получаем или создаем пользователя
        defaults = {
            'phone': social_data.phone,
            'first_name': social_data.first_name,
            'last_name': social_data.last_name,
            'middle_name': social_data.middle_name
        }

        # Проверка типа аккаунта, отсылаемого при авторизации
        if account_type is not None and AccountType.has_value(account_type):
            defaults['account_type'] = account_type

        if base_user is None or base_user.is_anonymous:
            # Если запрос пришел без авторизации (регистрация и содание аккаунта через соцсеть)
            result, created = cls.social_registration(social, social_data, defaults, account_type)

        else:
            # Если происходит привязка соцсети к аккаунту
            created = False
            result = cls.social_attaching(social, social_data, base_user)

        return result, created


class SocialsRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__(SocialModel)

    @staticmethod
    def create(**kwargs):
        return SocialModel.objects.create(**kwargs)


class JwtRepository:
    def __init__(self, headers=None):
        self.app_version = headers['App'] if headers and 'App' in headers else None
        self.platform_name = headers['Platform'] if headers and 'Platform' in headers else None
        self.vendor = headers['Vendor'] if headers and 'Vendor' in headers else None

    @classmethod
    def get_or_create_jwt_token(cls, user: UserProfile):
        try:
            return cls.get_jwt_token(user)
        except EntityDoesNotExistException:
            return cls().create_jwt_token(user)

    def create_jwt_token(self, user: UserProfile):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(
            user=user, access_token=access_token, refresh_token=refresh_token, app_version=self.app_version,
            platform_name=self.platform_name, vendor=self.vendor
        )

    @staticmethod
    def get_jwt_token(user: UserProfile):
        try:
            return JwtToken.objects.get(user=user)
        except JwtToken.DoesNotExist:
            raise EntityDoesNotExistException()

    @staticmethod
    def remove_old(user):
        JwtToken.objects.filter(**{'user_id': user.id}).delete()

    @staticmethod
    def refresh(refresh_token, new_access_token):
        # TODO нужно доработать, если потребуется ROTATE_REFRESH_TOKENS=True и BLACKLIST_AFTER_ROTATION=True
        pair = JwtToken.objects.filter(**{'refresh_token': refresh_token}).first()
        if pair:
            pair.access_token = new_access_token
            pair.save()

        return pair

    def create_jwt_pair(self, user):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(
            **JwtTokenEntity(
                user, access_token, refresh_token, self.app_version, self.platform_name, self.vendor
            ).get_kwargs()
        )

    @staticmethod
    def get_user(token):
        try:
            return JwtToken.objects.get(access_token=token).user
        except JwtToken.DoesNotExist:
            raise EntityDoesNotExistException()

    @staticmethod
    def get_jwt_pair(user):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(**JwtTokenEntity(user, access_token, refresh_token).get_kwargs())


class AsyncJwtRepository(JwtRepository):
    def __init__(self) -> None:
        super().__init__()

    @database_sync_to_async
    def get_user(self, token):
        return super().get_user(token)


class ProfileRepository(MasterRepository):
    model = UserProfile

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def get_by_username(self, username):
        try:
            return self.model.objects.get(username=username)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Логин введен неверно'
            )

    def get_by_username_and_password(self, validated_data):
        user = self.get_by_username(username=validated_data['username'])
        if not user.check_password(validated_data['password']):
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Пароль введен неверно'
            )
        return user


class AsyncProfileRepository(ProfileRepository):
    def __init__(self) -> None:
        super().__init__()

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)

    @database_sync_to_async
    def update_location(self, user: UserProfile, lon, lat):
        return super().update_location(user, lon, lat)


class NotificationsRepository(MasterRepository):
    model = Notification


class FCMDeviceRepository(MasterRepository):
    model = FCMDevice


class NotificationsSettingsRepository(MasterRepository):
    model = NotificationsSettings


class CareerRepository(MasterRepository):
    model = UserCareer


class DocumentsRepository(MasterRepository):
    model = Document

    def update_media(self, instance, files_uuid, me):
        if files_uuid is not None and isinstance(files_uuid, list):  # Обрабатываем только массив
            try:
                # Отфильтровываем невалидные uuid
                files_uuid = list(filter(lambda x: is_valid_uuid(x), files_uuid))

                user_ct = ContentType.objects.get_for_model(me)
                document_ct = ContentType.objects.get_for_model(instance)
                # Получаем массив uuid всех прикрепленных к документу файлов

                # Получаем массив uuid файлов которые прикреплены к документу но не пришли в списке прикрепляемых
                # и перепривязываем их к обратно пользователю (или удаляем)
                instance.media \
                    .all() \
                    .exclude(uuid__in=files_uuid) \
                    .update(deleted=True)

                # Получаем из бд массив загруженных файлов, которые нужно прикрепить к документу
                # Получаем список файлов

                # Находим список всех прикрепленных файлов
                # Добавляем или обновляем языки пользователя
                MediaRepository().filter(
                    Q(uuid__in=files_uuid, owner_ct=document_ct, owner_id=instance.id) |
                    Q(uuid__in=files_uuid, owner_ct=user_ct, owner_id=me.id)
                ).update(
                    updated_at=now(),
                    owner_ct=document_ct,
                    owner_ct_name=document_ct.model,
                    owner_id=instance.id
                )
            except Exception as e:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.UNSUPPORTED_FILE_FORMAT, **{'detail': str(e)}))
                ])
