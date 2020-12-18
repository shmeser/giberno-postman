from app_users.entities import TokenEntity, SocialEntity
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.utils import timestamp_to_datetime, has_latin


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

        entity.social_type = data.get('firebase').get('sign_in_provider', 'firebase')
        entity.access_token_expiration = timestamp_to_datetime(
            data.get('exp', None), milliseconds=False
        ) if data.get('exp', None) is not None else None
        entity.phone = data.get('phone_number', None)
        entity.email = data.get('email', None)
        entity.username = data.get('name', None)
        identities = data.get('firebase').get('identities', None) if 'firebase' in data else None
        if identities:
            entity.social_id = identities[entity.social_type][0] if entity.social_type in identities and identities[
                entity.social_type] else None
            entity.email = identities['email'][0] if 'email' in identities and identities['email'] else None
            entity.first_name = identities['first_name'][0] if 'first_name' in identities and identities[
                'first_name'] else None
            entity.last_name = identities['last_name'][0] if 'last_name' in identities and identities[
                'last_name'] else None

        # Проверка ФИО на латиницу, если используется, то не подставляем данные
        entity.first_name = None if has_latin(entity.first_name) else entity.first_name
        entity.last_name = None if has_latin(entity.last_name) else entity.last_name
        entity.middle_name = None if has_latin(entity.middle_name) else entity.middle_name

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
