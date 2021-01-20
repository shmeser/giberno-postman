from rest_framework.permissions import SAFE_METHODS

from app_users.permissions import FilledProfilePermission
from backend.utils import user_is_admin


class AbbleToPerform(FilledProfilePermission):

    def has_permission(self, request, view=None):
        """
        метод, вызываемый автоматически при каждом запросе.
        """
        super().has_permission(request, view)

        if request.method in SAFE_METHODS:
            return True

        is_user_allowed = self.__is_user_allowed(request, view)

        return is_user_allowed or user_is_admin(request.user)

    def has_object_permission(self, request, view, obj):
        """
        метод, вызываемый для проверки запрашеваемого объекта
        к запрашевоемому действию.
        """

        is_user_allowed = self.__is_user_allowed(request, view)

        owner_field_name = view.owner_field_name

        return ((self.__user_is_owner(request.user, obj, owner_field_name) and
                 is_user_allowed) or user_is_admin(request.user))

    def __get_required_permissions(self, request, view):
        """
        метод пытается достать перечисленные разрешения указанные в методе
        класса APIView.

        если таковых не находится, он возращает автоматически сгенерированное
        разрешение на основе HTTP метода запроса.
        """
        try:
            return view.required_permissions
        except Exception:
            pass
        actions = {
            'GET': 'view',
            'OPTIONS': 'view',
            'HEAD': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete'
        }
        app_name = view.serializer_class.Meta.model._meta.app_label
        model_name = view.serializer_class.Meta.model._meta.model_name
        return app_name + '.' + actions[request.method] + '_' + model_name

    def __user_is_owner(self, user, obj, owner_field_name: str):
        try:
            return getattr(obj, owner_field_name) == user
        except AttributeError:
            return False

    def __is_user_allowed(self, request, view):
        """
        метод расчитывает, позволено ли пользователю запрошенное действие.
        """
        if request.method in SAFE_METHODS:
            return True

        permissions = self.__get_required_permissions(request, view)
        # включая права групп, в которых состоит пользователь
        user_permissions = list(request.user.get_all_permissions())
        if type(permissions) == str:  # если разрешение было сгенерированно автоматически
            return True if permissions in user_permissions else False

        # True если пользователь имеет все права перечисленные
        # в 'user_permissions'
        return all([True if i in permissions else False for i in user_permissions])
