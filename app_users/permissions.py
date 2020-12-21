from rest_framework import permissions

from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException, CustomException
from app_users.models import UserProfile


class FilledProfilePermission(permissions.IsAuthenticated):
    ALLOWED_ENDPOINTS = [
        {'method': 'GET', 'url': '/api/geo/countries'},
    ]

    def has_permission(self, request, view=None):
        endpoint = {'method': request.method, 'url': request.path}
        if endpoint in self.ALLOWED_ENDPOINTS:
            return True
        # if request.user.is_authenticated:
        #     if request.user.is_superuser or request.user.is_staff:
        #         return True
        user = UserProfile.objects.filter(
            pk=request.user.pk,
            name__isnull=False,
            city_id__isnull=False).exclude(name='').exclude(email='')
        if user.exists():
            if user.first().deleted:
                raise HttpException(detail=RESTErrors.NOT_AUTHORIZED.name, status_code=RESTErrors.NOT_AUTHORIZED.value)
            return True
        else:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.SOCIAL_ALREADY_IN_USE))
            ])
