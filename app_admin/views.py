from rest_framework.views import APIView

from app_admin.versions.v1_0 import views as v1_0
from app_users.permissions import IsAdminOrManager
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException


class Staff(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.Staff().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.Staff().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class StaffMember(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.StaffMember().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.StaffMember().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.StaffMember().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class AccessContentTypes(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.AccessContentTypes().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class UsersAccess(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.UsersAccess().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.UsersAccess().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class UserAccess(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.UserAccess().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def put(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.UserAccess().put(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.UserAccess().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ApiKeys(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.ApiKeys().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def post(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.ApiKeys().post(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)


class ApiKey(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.ApiKey().get(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)

    @staticmethod
    def delete(request, **kwargs):
        if request.version in ['admin_1_0']:
            return v1_0.ApiKey().delete(request, **kwargs)
        raise HttpException(status_code=RESTErrors.NOT_FOUND, detail=ErrorsCodes.METHOD_NOT_FOUND.value)
