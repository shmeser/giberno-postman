from app_users.entities import TokenEntity, SocialEntity
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.utils import timestamp_to_datetime, has_latin, nonefy, chained_get


class TokensMapper:
    @staticmethod
    def firebase(data):
        if data.get('firebase_token') is None:
            raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)

        return TokenEntity(token=data.get('firebase_token'))

    @staticmethod
    def vk(data):
        if data.get('vk_token') is None:
            raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)

        return TokenEntity(token=data.get('vk_token'))


class SocialDataMapper:
    @staticmethod
    def firebase(data):
        entity = SocialEntity()

        entity.firebase_id = data.get('uid', None)

        entity.social_type = chained_get(data, 'firebase', 'sign_in_provider', default='firebase')
        entity.access_token_expiration = timestamp_to_datetime(
            data.get('exp', None), milliseconds=False
        ) if data.get('exp') is not None else None

        entity.phone = data.get('phone_number')
        entity.email = data.get('email')
        entity.username = data.get('name')
        identities = chained_get(data, 'firebase', 'identities')
        if identities:
            # TODO проверить Apple и Facebook
            entity.social_id = chained_get(identities, entity.social_type, 0)
            entity.email = chained_get(identities, 'email', 0)
            entity.first_name = chained_get(identities, 'first_name', 0)
            entity.last_name = chained_get(identities, 'last_name', 0)

        # Проверка ФИО на латиницу, если используется, то не подставляем данные
        entity.first_name = nonefy(entity.first_name, has_latin(entity.first_name))
        entity.last_name = nonefy(entity.last_name, has_latin(entity.last_name))
        entity.middle_name = nonefy(entity.middle_name, has_latin(entity.middle_name))

        return entity

    @staticmethod
    def vk(data):
        entity = SocialEntity()

        entity.social_id = data.get('id', None)
        entity.social_type = data.get('type', None)
        entity.access_token = data.get('access_token', None)
        entity.access_token_expiration = timestamp_to_datetime(
            data.get('expires_in', None), milliseconds=False
        ) if data.get('expires_in', None) is not None else None
        entity.phone = data.get('phone_number', None)
        entity.email = data.get('email', None)
        entity.first_name = data.get('first_name', None)
        entity.last_name = data.get('last_name', None)
        entity.middle_name = data.get('middle_name', None)
        entity.username = data.get('screen_name', None)

        # Проверка ФИО на латиницу, если используется, то не подставляем данные
        entity.first_name = None if has_latin(entity.first_name) else entity.first_name
        entity.last_name = None if has_latin(entity.last_name) else entity.last_name
        entity.middle_name = None if has_latin(entity.middle_name) else entity.middle_name

        return entity
