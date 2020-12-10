from datetime import timedelta

from django.utils.timezone import now

from app_users.entities import SocialEntity
from app_users.mappers import SocialDataMapper
from app_users.models import SocialModel
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import SocialModelRepository, AuthRepository
from app_users.versions.v1_0.repositories import UsersRepository
# from backend.utils import CP
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException


def exchange_access_token(backend, details, response, *args, **kwargs):
    """ Получаем для инстаграма долгосрочный токен """
    if backend.name == 'instagram':
        long_lived_access_token = backend.get_long_lived_access_token(access_token=response['access_token'])
        if long_lived_access_token:
            # Заменяем короткосрочный токен долгосрочным
            response['access_token'] = long_lived_access_token.get('access_token')
            # Заменяем поле времени
            response['expires'] = long_lived_access_token.get('expires_in')

    kwargs.update({'response': response})


def get_or_create_user(backend, user: UserProfile = None, *args, **kwargs):
    if user and not user.is_anonymous:  # в пайплайн приходит AnonymousUser если не передать своего
        if backend.name == 'vk-oauth2':
            social_data: SocialEntity = SocialDataMapper.vk(kwargs.get('response'))
            social_data.access_token_expiration = now() + timedelta(seconds=kwargs.get('response').get('expires_in'))
            social_data.social_type = backend.name
        else:
            social_data = SocialEntity()

        social = SocialModelRepository().filter_by_kwargs(type=backend.name, social_id=kwargs.get('uid')).first()

        if not social:
            # Создаем модель способа авторизации
            SocialModelRepository().create(
                user=user,
                type=backend.name,
                social_id=kwargs.get('uid'),
                access_token=kwargs.get('response').get('access_token'),
                access_token_expiration=now() + timedelta(seconds=kwargs.get('response').get('expires'))
            )
            # TODO если долгосрочный access_token протух, то выдавать ошибку чтоб перепривязали соцсеть
            # TODO добавить шедулер, по которому будет обновляться долгосрочный токен инстаграма
        else:
            if social.user.id != user.id:
                raise HttpException(detail='Данным способом уже зарегистрирован другой пользователь',
                                    status_code=RESTErrors.ANOTHER_USER_HAS_SAME_SOCIAL)
            # Обновляем access_token
            social.access_token = kwargs.get('response').get('access_token')
            social.access_token_expiration = now() + timedelta(seconds=kwargs.get('response').get('expires'))
            social.save()
        return {
            'is_new': False,
            'user': user
        }
    else:
        if backend.name == 'vk-oauth2':
            social_data: SocialEntity = SocialDataMapper.vk(kwargs.get('response'))
            social_data.access_token_expiration = now() + timedelta(seconds=kwargs.get('response').get('expires_in'))
            social_data.social_type = backend.name
        else:
            social_data = SocialEntity()

        social = SocialModelRepository().filter_by_kwargs(type=backend.name,social_id=kwargs.get('uid')).first()

        if social:
            """ Если соцсеть привязана к чьему-либо аккаунту, то берем этот аккаунт """
            user = social.user
        else:
            """ Если такой соцсети нет, то создать пользователя и добавить ему эту соцсеть """
            user, created = AuthRepository.get_or_create_social_user(
                social_data,
                # account_type=body.get('account_type', AccountType.SELF_EMPLOYED),
                # reference_code=body.get('reference_code', None)
            )

        # TODO добавить добавление имени фамилии пола возраста и фото из фейсбука
        user.provider = backend.name  # Необходимо добавить провайдера в user для использования web авторизации

    return {
        'social': user,
        'is_new': True,
        'user': user
    }
