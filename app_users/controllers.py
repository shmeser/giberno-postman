import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin._token_gen import ExpiredIdTokenError

from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException


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
                    detail=RESTErrors.INVALID_ACCESS_TOKEN.name,
                    status_code=RESTErrors.INVALID_ACCESS_TOKEN
                )
        except ValueError:
            raise HttpException(
                detail=RESTErrors.INVALID_ACCESS_TOKEN.name,
                status_code=RESTErrors.INVALID_ACCESS_TOKEN
            )
        except ExpiredIdTokenError as e:
            raise HttpException(detail=e, status_code=RESTErrors.INVALID_ACCESS_TOKEN)
        except Exception as e:
            raise HttpException(detail=e, status_code=RESTErrors.INVALID_ACCESS_TOKEN)

        return decoded_token
