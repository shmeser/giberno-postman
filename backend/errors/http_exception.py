from django.utils.encoding import force_text
from rest_framework.exceptions import APIException

from .enums import RESTErrors


class HttpException(APIException):
    default_detail = RESTErrors.INTERNAL_SERVER_ERROR.name
    default_code = RESTErrors.INTERNAL_SERVER_ERROR

    def __init__(self, detail=None, status_code=None):
        self.status_code = status_code
        if detail is None:
            detail = force_text(self.default_detail)
        if status_code is None:
            status_code = self.default_code
        super(HttpException, self).__init__(detail, status_code)


class CustomException(APIException):
    default_detail = RESTErrors.CUSTOM_DETAILED_ERROR.name
    default_code = RESTErrors.CUSTOM_DETAILED_ERROR

    def __init__(self, errors: list = None, detail=None, status_code=default_code):
        self.status_code = status_code
        self.errors = errors
        if detail is None:
            detail = force_text(self.default_detail)
        if status_code is None:
            status_code = self.default_code
        super(CustomException, self).__init__(detail, status_code)
