from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, ExpressionWrapper, Exists, OuterRef, BooleanField, Subquery, Count, Window, Max, \
    F, IntegerField, Case, When, DateField
from django.db.models.functions import Coalesce, Trunc
from django.utils.timezone import now

from app_admin.models import AccessUnit, AccessRight
from app_games.enums import Grade, TaskKind, TaskPeriod
from app_games.models import Prize, Task, UserFavouritePrize, UserPrizeProgress, PrizeCardsHistory, PrizeCard, UserTask, \
    GoodsCategory
from app_market.enums import Currency
from app_market.models import Structure, Distributor, Shop, Vacancy, Shift, ShiftAppeal, Organization
from app_market.versions.v1_0.repositories import ShiftAppealsRepository
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_users.enums import AccountType
from app_users.models import UserMoney, UserProfile
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException, CustomException
from backend.mixins import MasterRepository
from giberno.settings import MAX_AMOUNT_FOR_PREFERRED_DEFAULT_GRADE_PRIZES


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
