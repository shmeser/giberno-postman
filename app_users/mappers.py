from app_users.entities import TokenEntity
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException


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
