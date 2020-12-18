from rest_framework_simplejwt.tokens import RefreshToken

from app_users.entities import JwtTokenEntity, SocialEntity
from app_users.enums import AccountType
from app_users.models import SocialModel, UserProfile, JwtToken
from backend.errors.enums import RESTErrors
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from backend.repositories import BaseRepository


class UsersRepository:
    @staticmethod
    def get_reference_user(reference_code):
        return UserProfile.objects.filter(uuid__icontains=reference_code, deleted=False).first()


class AuthRepository:

    @staticmethod
    def get_or_create_social_user(social_data: SocialEntity, account_type=AccountType.SELF_EMPLOYED,
                                  reference_code=None):

        # Проверка реферального кода
        reference_user = None
        if reference_code:
            reference_user = UsersRepository.get_reference_user(reference_code)
            if reference_user is None:
                raise HttpException(detail='Невалидный реферальный код', status_code=RESTErrors.BAD_REQUEST)

        # Создаем способ авторизации
        social, created = SocialModel.objects.get_or_create(
            social_id=social_data.social_id, type=social_data.social_type, defaults=social_data.get_kwargs()
        )

        # Получаем или создаем пользователя
        defaults = {
            'reg_reference': reference_user,
            'reg_reference_code': reference_code,
            'phone': social_data.phone,
            'first_name': social_data.first_name,
            'last_name': social_data.last_name,
            'middle_name': social_data.middle_name,
            'username': social_data.username,
        }

        # Проверка типа аккаунта, отсылаемого при авторизации
        if account_type is not None and AccountType.has_value(account_type):
            defaults['account_type'] = account_type

        user, created = UserProfile.objects.get_or_create(socialmodel=social, defaults=defaults)

        if created:
            # Привязываем пользователя к соцсети
            social.user = user
            social.save()
            user.email = social_data.email
        else:
            # Подставляем имеил с соцсети, если его нет
            if not user.email and social_data.email:
                user.email = social_data.email
        user.save()

        if user.account_type != account_type:
            raise HttpException(
                detail='Данным способом уже зарегистрирован пользователь с другой ролью',
                status_code=RESTErrors.FORBIDDEN
            )

        # Создаем модель настроек
        # TODO
        return user, created


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


class ProfileRepository(MasterRepository):
    model = UserProfile

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail='Объект %s с ID=%d не найден' % (self.model._meta.verbose_name, record_id)
            )
