from rest_framework import permissions

from app_users.enums import AccountType
from app_users.models import UserProfile
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException, CustomException


class FilledProfilePermission(permissions.IsAuthenticated):
    ALLOWED_ENDPOINTS = [
        {'method': 'GET', 'url': '/api/geo/countries'},
    ]

    def has_permission(self, request, view=None):
        endpoint = {'method': request.method, 'url': request.path}
        if endpoint not in self.ALLOWED_ENDPOINTS:
            return False
        user = UserProfile.objects.filter(
            pk=request.user.pk,
            name__isnull=False,
            city_id__isnull=False).exclude(name='').exclude(email='')
        if user.exists():
            if user.first().deleted:
                raise HttpException(detail=RESTErrors.NOT_AUTHORIZED.name, status_code=RESTErrors.NOT_AUTHORIZED.value)
        else:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.SOCIAL_ALREADY_IN_USE))
            ])
        return True


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.account_type == AccountType.ADMIN


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.account_type == AccountType.MANAGER


class IsManagerOrSecurity(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.account_type == AccountType.MANAGER or request.user.account_type == AccountType.SECURITY


class IsSelfEmployed(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.account_type == AccountType.SELF_EMPLOYED
