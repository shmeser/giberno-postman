from django.contrib.contenttypes.models import ContentType

from django.contrib.contenttypes.models import ContentType

from app_admin.models import AccessUnit, AccessRight, ApiKeyToken
from app_market.models import Structure, Distributor, Shop, Vacancy, Shift, ShiftAppeal, Organization
from app_users.enums import AccountType
from app_users.models import UserProfile
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository


class UserAccessRepository(MasterRepository):
    model = AccessUnit

    def __init__(self, me=None) -> None:
        super().__init__()

        self.me = me

    def get_access(self, record_id):
        # TODO проверять разрешения
        results = self.model.objects.filter(id=record_id).exclude(deleted=True)
        result = results.first()
        if not result:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )
        return result

    @staticmethod
    def get_available_content_types():
        content_types = ContentType.objects.get_for_models(
            Structure,
            Distributor,
            Shop,
            Vacancy,
            Shift,
            ShiftAppeal,
            Organization,
            UserProfile
        )
        return content_types.values()

    @staticmethod
    def get_user_access_units(user_id):
        return AccessUnit.objects.filter(user_id=user_id, deleted=False).select_related('access_right')

    def get_access_rights(self, user_id):
        users = UserProfile.objects.filter(id=user_id).exclude(deleted=True)
        user = users.first()
        if not user:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {UserProfile._meta.verbose_name} с ID={user_id} не найден'
            )

        access_units = self.get_user_access_units(user.id)

        return access_units

    @staticmethod
    def add_access(data):
        user = UserProfile.objects.filter(id=data.get('user')).first()
        if not user:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {UserProfile._meta.verbose_name} с ID={data.get("user")} не найден'
            )

        try:
            object_ct = ContentType.objects.get_for_id(data.get('object_ct_id'))
            object_ct_name = object_ct.model
        except:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {ContentType._meta.verbose_name} с ID={data.get("object_ct_id")} не найден'
            )

        object_id = data.get('object_id')
        has_access = data.get('has_access', False)

        access_right = data.get('access_right')

        unit, created = AccessUnit.objects.get_or_create(
            defaults={
                'object_ct_name': object_ct_name,
                'has_access': has_access
            },
            user=user,
            object_ct=object_ct,
            object_id=object_id,

        )
        if access_right and created:
            AccessRight.objects.create(
                unit=unit,
                user=user,
                **access_right
            )
        if access_right and not created:
            unit.deleted = False
            unit.save()

    @staticmethod
    def add_access_right(instance, data):
        if data and instance:
            AccessRight.objects.create(
                unit=instance,
                user=instance.user,
                **data
            )
            instance.deleted = False
            instance.save()

    @staticmethod
    def get_staff(paginator):
        staff = UserProfile.objects.filter(
            deleted=False
        ).exclude(account_type=AccountType.SELF_EMPLOYED.value).exclude(is_superuser=True)
        result = staff[paginator.offset:paginator.limit] if paginator else staff
        count = staff.count()
        return result, count

    def get_staff_member(self, record_id):
        results = UserProfile.objects.filter(id=record_id).exclude(
            deleted=True, account_type=AccountType.SELF_EMPLOYED.value
        )

        result = results.first()
        if not result:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {UserProfile._meta.verbose_name} с ID={record_id} не найден'
            )
        return result


class ApiKeysRepository(MasterRepository):
    model = ApiKeyToken

    def __init__(self, me=None) -> None:
        super().__init__()

        self.me = me

    def get_keys(self, kwargs, order, paginator):
        records = ApiKeyToken.objects.filter(**kwargs)
        if order:
            records = records.order_by(order)
        count = records.count()
        result = records[paginator.offset:paginator.limit] if paginator else records
        return result, count

    @staticmethod
    def add_key(data):
        organization = Organization.objects.filter(id=data.get('organization')).first()
        if not organization:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {Organization._meta.verbose_name} с ID={data.get("organization")} не найден'
            )

        api_key, created = ApiKeyToken.objects.get_or_create(
            organization=organization,
            deleted=False
        )
        return api_key

    @staticmethod
    def get_key(record_id):
        results = ApiKeyToken.objects.filter(id=record_id).exclude(
            deleted=True
        )

        result = results.first()
        if not result:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {ApiKeyToken._meta.verbose_name} с ID={record_id} не найден'
            )
        return result
