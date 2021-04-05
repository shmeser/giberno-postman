from rest_framework.response import Response
from rest_framework.views import exception_handler

from backend.errors.http_exceptions import CustomException


def custom_exception_handler(exc, context):
    if isinstance(exc, CustomException):
        data = {
            'errors': exc.errors
        }
        return Response(data=data, status=exc.status_code)

    return exception_handler(exc, context)
