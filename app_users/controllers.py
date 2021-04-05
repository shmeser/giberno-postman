import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin._token_gen import ExpiredIdTokenError

from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException


class FirebaseController:
    @classmethod
    def verify_token(cls, firebase_token):
        if not len(firebase_admin._apps):
            cred = credentials.Certificate('account.json')
            firebase_admin.initialize_app(cred)

        try:
            decoded_token = firebase_auth.verify_id_token(firebase_token)
            if decoded_token is None:
                raise HttpException(
                    detail='Невалидный access_token',
                    status_code=RESTErrors.NOT_AUTHORIZED
                )
        except ValueError as e:
            raise HttpException(
                detail=str(e),
                status_code=RESTErrors.NOT_AUTHORIZED
            )
        except ExpiredIdTokenError as e:
            raise HttpException(detail=e, status_code=RESTErrors.NOT_AUTHORIZED)
        except Exception as e:
            raise HttpException(detail=e, status_code=RESTErrors.NOT_AUTHORIZED)

        return decoded_token
