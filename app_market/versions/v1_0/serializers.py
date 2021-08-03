from datetime import datetime

import pytz
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Avg, Sum, Count, Q, F
from django.db.models.functions import Coalesce
from django.utils.timezone import localtime
from pytz import timezone
from rest_framework import serializers

from app_market.enums import ShiftAppealStatus, ManagerAppealCancelReason, SecurityPassRefuseReason, \
    FireByManagerReason, AppealCompleteReason, FinancesInterval, Currency, OrderType
from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, Category, ShiftAppeal, Partner, \
    Achievement, Advertisement, Order, Coupon, Transaction, ShiftAppealInsurance
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShiftsRepository
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.controllers import MediaController
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.enums import REQUIRED_DOCS_DICT
from app_users.models import UserProfile
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer
from backend.utils import chained_get, datetime_to_timestamp, timestamp_to_datetime, ArrayRemove, choices


def map_status_for_required_docs(required_docs, user_docs):
    documents = []
    for r_d in required_docs:
        doc = {
            'title': REQUIRED_DOCS_DICT[r_d],
            'type': r_d,
            'is_confirmed': r_d in user_docs if user_docs else False
        }
        documents.append(doc)

    return documents


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id', 'title'
        ]


class DistributorsSerializer(CRUDSerializer):
    repository = DistributorsRepository

    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    categories = serializers.SerializerMethodField()
    vacancies_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.LOGO.value)

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.BANNER.value)

    def get_categories(self, prefetched_data):
        return CategoriesSerializer(prefetched_data.categories, many=True).data

    def get_vacancies_count(self, prefetched_data):
        return chained_get(prefetched_data, 'vacancies_count')

    def get_rating(self, instance):
        return instance.reviews.all().aggregate(avg=Avg('value'))['avg']

    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
            'description',
            'vacancies_count',
            'rates_count',
            'rating',
            'categories',
            'logo',
            'banner'
        ]


class ShopsSerializer(CRUDSerializer):
    """ Список магазинов """
    walk_time = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def get_lon(self, instance):
        return instance.location.x if instance.location else None

    def get_lat(self, instance):
        return instance.location.y if instance.location else None

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.LOGO.value)

    def get_walk_time(self, shop):
        if chained_get(shop, 'distance'):
            # Принимаем среднюю скорость пешеходов за 3.6км/ч = 1м/с
            # Выводим расстояние в метрах как количество секунд
            return int(shop.distance.m)
        return None

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'walk_time',
            'time_start',
            'time_end',
            'lon',
            'lat',
            'logo',
        ]


class ShopSerializer(ShopsSerializer):
    """ Магазин """
    banner = serializers.SerializerMethodField()
    vacancies_count = serializers.SerializerMethodField()

    def get_vacancies_count(self, prefetched_data):
        return chained_get(prefetched_data, 'vacancies_count')

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.BANNER.value)

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'walk_time',
            'time_start',
            'time_end',
            'vacancies_count',
            'rating',
            'rates_count',
            'lon',
            'lat',
            'logo',
            'banner',
        ]


class ShopInVacancySerializer(ShopsSerializer):
    """ Вложенная модель магазина в вакансии (на экране просмотра одной вакансии) """

    map = serializers.SerializerMethodField()

    def get_map(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.MAP.value)

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'walk_time',
            'time_start',
            'time_end',
            'rating',
            'rates_count',
            'lon',
            'lat',
            'logo',
            'map',
        ]


class ShopInVacancyShiftSerializer(ShopsSerializer):
    """ Вложенная модель магазина в вакансии (на экране просмотра откликов по вакансиям) """
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def get_lon(self, instance):
        return instance.location.x if instance.location else None

    def get_lat(self, instance):
        return instance.location.y if instance.location else None

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'address',
            'lon',
            'lat',
            'walk_time',
            'logo',
        ]


class DistributorInVacancySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.LOGO.value)

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.BANNER.value)

    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
            'logo',
            'banner',
        ]


class VacanciesSerializer(CRUDSerializer):
    repository = VacanciesRepository

    is_favourite = serializers.SerializerMethodField()
    is_hot = serializers.SerializerMethodField()
    work_time = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()
    distributor = serializers.SerializerMethodField()
    utc_offset = serializers.SerializerMethodField()
    free_count = serializers.SerializerMethodField()

    banner = serializers.SerializerMethodField()

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.BANNER.value)

    def get_is_favourite(self, vacancy):
        return vacancy.is_favourite

    def get_utc_offset(self, vacancy):
        return pytz.timezone(vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds()

    def get_is_hot(self, vacancy):
        return vacancy.is_hot

    def get_free_count(self, vacancy):
        return vacancy.free_count

    def get_work_time(self, vacancy):
        return vacancy.work_time

    def get_shop(self, vacancy):
        return ShopsSerializer(vacancy.shop).data

    def get_distributor(self, vacancy):
        if vacancy.shop and vacancy.shop.distributor:
            return DistributorInVacancySerializer(vacancy.shop.distributor).data
        return None

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'description',
            'price',
            'is_favourite',
            'is_hot',
            'utc_offset',
            'free_count',
            'rating',
            'required_experience',
            'employment',
            'work_time',
            'banner',
            'shop',
            'distributor',
        ]


class VacancyInCluster(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    walk_time = serializers.SerializerMethodField()

    address = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def get_id(self, data):
        return chained_get(data, 'id')

    def get_title(self, data):
        return chained_get(data, 'title')

    def get_lon(self, data):
        return chained_get(data, 'lon')

    def get_lat(self, data):
        return chained_get(data, 'lat')

    def get_price(self, data):
        return chained_get(data, 'price')

    def get_address(self, data):
        return chained_get(data, 'address')

    def get_walk_time(self, data):
        return chained_get(data, 'distance')

    def get_logo(self, data):
        return chained_get(data, 'logo')

    def get_banner(self, data):
        return chained_get(data, 'banner')


class VacanciesClusterSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    clustered_count = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    vacancies = serializers.SerializerMethodField()

    def get_id(self, data):
        return chained_get(data, 'cid')

    def get_clustered_count(self, data):
        return chained_get(data, 'clustered_count')

    def get_lon(self, data):
        return chained_get(data, 'lon')

    def get_lat(self, data):
        return chained_get(data, 'lat')

    def get_vacancies(self, data):
        vacancies = chained_get(data, 'clustered_items')
        return VacancyInCluster(
            vacancies, many=True, context=self.context
        ).data

    class Meta:
        fields = [
            'id',
            'clustered_count',
            'lon',
            'lat',
            'title',
            'price',
            'banner',
            'shop',
        ]


class VacancySerializer(VacanciesSerializer):
    created_at = DateTimeField()
    utc_offset = serializers.SerializerMethodField()
    required_docs = serializers.SerializerMethodField()

    def get_shop(self, vacancy):
        return ShopInVacancySerializer(vacancy.shop).data

    def get_required_docs(self, vacancy):
        if not vacancy.required_docs:
            return []
        return map_status_for_required_docs(
            vacancy.required_docs,
            self.me.documents.aggregate(
                docs=ArrayRemove(
                    ArrayAgg('type', distinct=True), None
                )
            )['docs']
        )

    def get_utc_offset(self, vacancy):
        return pytz.timezone(vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds()

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'views_count',
            'rating',
            'rates_count',
            'free_count',
            'price',
            'features',
            'required_docs',
            'is_favourite',
            'is_hot',
            'utc_offset',
            'required_experience',
            'employment',
            'work_time',
            'banner',
            'shop',
            'distributor'
        ]


class VacancyForManagerSerializer(VacancySerializer):
    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'views_count',
            'rating',
            'rates_count',
            'free_count',
            'price',
            'features',
            'is_favourite',
            'is_hot',
            'utc_offset',
            'required_experience',
            'employment',
            'work_time',
            'banner',
            'shop',
            'distributor'
        ]


class VacancyInShiftSerializer(VacanciesSerializer):
    utc_offset = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()

    def get_utc_offset(self, vacancy):
        return pytz.timezone(vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds()

    def get_shop(self, instance):
        if instance.shop:
            return ShopInVacancyShiftSerializer(instance.shop, many=False).data
        return None

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'price',
            'radius',
            'utc_offset',
            'shop',
        ]


class VacancyInShiftForDocumentsSerializer(VacancyInShiftSerializer):
    distributor = serializers.SerializerMethodField()

    def get_distributor(self, instance):
        return DistributorInShiftSerializer(instance.shop.distributor, many=False).data

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'price',
            'utc_offset',
            'shop',
            'distributor'
        ]


class DistributorInShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
        ]


class UserProfileInVacanciesForManagerSerializer(CRUDSerializer):
    id = serializers.IntegerField()

    avatar = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_avatar(profile: UserProfile):
        # TODO надо префетчить
        avatar = MediaRepository().filter_by_kwargs({
            'owner_id': profile.id,
            'owner_ct_id': ContentType.objects.get_for_model(profile).id,
            'type': MediaType.AVATAR.value,
            'format': MediaFormat.IMAGE.value
        }, order_by=['-created_at']).first()
        if avatar:
            return MediaSerializer(avatar, many=False).data
        return None

    class Meta:
        model = UserProfile
        fields = ['id', 'avatar']


class VacanciesWithAppliersForManagerSerializer(CRUDSerializer):
    banner = serializers.SerializerMethodField()

    @staticmethod
    def get_banner(instance):
        return MediaController(instance).get_related_images(instance, MediaType.BANNER.value)

    total_count = serializers.SerializerMethodField()

    def get_total_count(self, instance):
        return self.get_max_count(instance=instance)

    free_count = serializers.SerializerMethodField()

    def get_free_count(self, instance):
        return self.get_max_count(instance=instance) - self.get_employees_count(instance=instance)

    appliers_count = serializers.SerializerMethodField()

    def get_appliers_count(self, instance):
        return self.active_appeals(instance=instance).count()

    appliers = serializers.SerializerMethodField()

    def get_appliers(self, instance):
        appliers = [appeal.applier for appeal in self.active_appeals(instance=instance)][:3]
        return UserProfileInVacanciesForManagerSerializer(instance=appliers, many=True).data

    def get_max_count(self, instance):
        queryset = self.active_shifts(instance=instance)
        if queryset.count():
            return queryset.aggregate(Sum('max_employees_count')).get('max_employees_count__sum', 0)
        return 0

    def get_employees_count(self, instance):
        queryset = self.active_shifts(instance=instance)
        if queryset.count():
            return queryset.annotate(
                timezone=F('vacancy__timezone')
            ).aggregate(
                count=Coalesce(
                    Count(
                        'appeals',
                        filter=Q(
                            appeals__shift_active_date__datetz=localtime(
                                self.context.get('current_date'), timezone=timezone(instance.timezone)
                            ).date(),
                            appeals__status=ShiftAppealStatus.CONFIRMED.value
                        )
                    ), 0
                )
            ).get('count', 0)
        return 0

    def active_shifts(self, instance):
        active_shifts_ids_by_date = []
        shifts = ShiftsRepository(
            calendar_from=self.context.get('current_date'),
            calendar_to=self.context.get('next_day')
        ).filter_by_kwargs({'vacancy': instance})
        for item in shifts:
            if self.context.get('current_date') in item.active_dates:
                active_shifts_ids_by_date.append(item.id)

        return Shift.objects.filter(id__in=list(set(active_shifts_ids_by_date)))

    def active_appeals(self, instance):
        return ShiftAppeal.objects.annotate(
            timezone=F('shift__vacancy__timezone')  # Добавляем временную зону для отклика из вакансии
        ).filter(
            shift__vacancy=instance,
            shift_active_date__datetz=localtime(  # должны совпадать даты в часовом поясе вакансии
                self.context.get('current_date'), timezone=timezone(instance.timezone)
            ).date(),
            **self.context.get('filters')
        )

    class Meta:
        model = Vacancy
        fields = ['id', 'title', 'banner', 'total_count', 'free_count', 'appliers_count', 'appliers']


class ShiftAppealCreateSerializer(CRUDSerializer):
    shift_active_date = serializers.IntegerField()

    @staticmethod
    def validate_shift_active_date(value):
        return timestamp_to_datetime(value)

    class Meta:
        model = ShiftAppeal
        fields = ['shift', 'shift_active_date']


class ShiftAppealsSerializer(CRUDSerializer):
    shift_active_date = DateTimeField()
    created_at = DateTimeField()
    time_start = DateTimeField()
    time_end = DateTimeField()
    fire_at = DateTimeField()

    shift = serializers.SerializerMethodField()
    vacancy = serializers.SerializerMethodField()

    def get_shift(self, instance):
        return ShiftsSerializer(instance.shift, many=False).data

    def get_vacancy(self, instance):
        if instance.shift.vacancy:
            return VacancyInShiftSerializer(instance.shift.vacancy, many=False).data
        return None

    class Meta:
        model = ShiftAppeal
        fields = [
            'id',
            'status',
            'shift_active_date',
            'time_start',
            'time_end',
            'created_at',
            'fire_at',
            'shift',
            'vacancy'
        ]


class ShiftsWithAppealsSerializer(CRUDSerializer):
    appliers = serializers.SerializerMethodField()

    def get_appliers(self, instance):
        appliers = ShiftsRepository().get_appeals_with_appliers(
            instance,
            self.context.get('current_date'),
            self.context.get('filters')
        )

        return UserProfileInVacanciesForManagerSerializer(instance=appliers, many=True).data

    confirmed_appliers = serializers.SerializerMethodField()

    def get_confirmed_appliers(self, instance):
        appliers = ShiftsRepository().get_appeals_with_appliers(
            instance,
            self.context.get('current_date'),
            {
                'status': ShiftAppealStatus.CONFIRMED
            }
        )
        return UserProfileInVacanciesForManagerSerializer(instance=appliers, many=True).data

    class Meta:
        model = Shift
        fields = ['id', 'time_start', 'time_end', 'max_employees_count', 'appliers', 'confirmed_appliers']


class ApplierSerializer(CRUDSerializer):
    id = serializers.IntegerField()
    birth_date = DateTimeField()

    avatar = serializers.SerializerMethodField(read_only=True)

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images(
            prefetched_data, MediaType.AVATAR.value, only_prefetched=True
        )

    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'birth_date', 'avatar']


class ShiftAppealsForManagersSerializer(CRUDSerializer):
    applier = serializers.SerializerMethodField()
    fire_at = DateTimeField()
    required_docs = serializers.SerializerMethodField()
    work_experience = serializers.SerializerMethodField()

    def get_applier(self, instance):
        return ApplierSerializer(instance.applier, many=False).data

    def get_required_docs(self, instance):
        if not instance.shift.vacancy.required_docs:
            return []
        return map_status_for_required_docs(instance.shift.vacancy.required_docs, instance.applier.documents_types)

    def get_work_experience(self, instance):
        cleaned_data = [{
            # Могут попадаться дубли, так как приходит UserShift
            # С данными по вакансии, а не сама вакансия
            # В одной вакансии может быть несколько разных смен, в которые работал пользователь
            'id': s.vacancy_id,
            'title': s.vacancy_title,
            'rating': s.total_rating,
            'rates_count': s.total_rates_count
        } for s in instance.applier.shifts]

        work_experience = list(  # Делаем список уникальных словарей
            {v['id']: v for v in cleaned_data}.values()
        )

        return work_experience

    class Meta:
        model = ShiftAppeal
        fields = ['id', 'status', 'fire_at', 'applier', 'required_docs', 'work_experience']


class ShiftsSerializer(CRUDSerializer):
    repository = ShiftsRepository

    active_dates = serializers.SerializerMethodField()
    active_today = serializers.SerializerMethodField()

    def get_active_dates(self, shift):
        if chained_get(shift, 'active_dates'):
            return list(map(lambda x: datetime_to_timestamp(x), shift.active_dates))
        return []

    def get_active_today(self, shift):
        return chained_get(shift, 'active_today')

    class Meta:
        model = Shift
        fields = [
            'id',
            # 'date_start',
            # 'date_end',
            'time_start',
            'time_end',
            'active_today',
            'active_dates'
        ]


class ShiftForManagersSerializer(serializers.ModelSerializer):
    confirmed_appeals_count = serializers.SerializerMethodField()
    vacancy_title = serializers.SerializerMethodField()

    def get_confirmed_appeals_count(self, data):
        return data.confirmed_appeals_count

    def get_vacancy_title(self, data):
        return data.vacancy.title

    class Meta:
        model = Shift
        fields = [
            'id',
            'time_start',
            'time_end',
            'confirmed_appeals_count',
            'max_employees_count',
            'vacancy_title'
        ]


class ProfessionSerializer(CRUDSerializer):
    repository = ProfessionsRepository

    class Meta:
        model = Profession
        fields = [
            'id',
            'name',
            'description',
        ]


class SkillSerializer(CRUDSerializer):
    repository = SkillsRepository

    class Meta:
        model = Skill
        fields = [
            'id',
            'name',
            'description',
        ]


# class VacancyInUserShiftSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Vacancy
#         fields = ['id', 'title', 'timezone']


# class UserShiftSerializer(serializers.ModelSerializer):
#     vacancy = serializers.SerializerMethodField()
#
#     @staticmethod
#     def get_vacancy(instance):
#         return VacancyInUserShiftSerializer(instance=instance.shift.vacancy).data
#
#     class Meta:
#         model = UserShift
#         exclude = ['created_at', 'updated_at', 'deleted']


class VacancyInConfirmedWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = ['id', 'title']


class ConfirmedWorkerProfessionsSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    @staticmethod
    def get_id(instance):
        return instance.shift.vacancy.profession_id

    @staticmethod
    def get_title(instance):
        return instance.shift.vacancy.profession.name

    class Meta:
        model = ShiftAppeal
        fields = ['id', 'title']


class ConfirmedWorkerDatesSerializer(serializers.ModelSerializer):
    real_time_start = serializers.SerializerMethodField()
    utc_offset = serializers.SerializerMethodField()

    def get_real_time_start(self, instance):
        return datetime_to_timestamp(instance.time_start)

    def get_utc_offset(self, instance):
        return pytz.timezone(instance.shift.vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds()

    class Meta:
        model = ShiftAppeal
        fields = ['real_time_start', 'utc_offset']


class ConfirmedWorkerSerializer(CRUDSerializer):
    id = serializers.IntegerField()
    birth_date = DateTimeField()

    avatar = serializers.SerializerMethodField(read_only=True)

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images(
            prefetched_data, MediaType.AVATAR.value, only_prefetched=False
        )

    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'birth_date', 'avatar']


class ConfirmedWorkersShiftsSerializer(serializers.ModelSerializer):
    shift_id = serializers.SerializerMethodField()
    vacancy = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    time_start = serializers.SerializerMethodField()
    time_end = serializers.SerializerMethodField()
    real_time_start = serializers.SerializerMethodField()
    real_time_end = serializers.SerializerMethodField()
    fire_at = DateTimeField()

    @staticmethod
    def get_shift_id(instance):
        return instance.shift_id

    @staticmethod
    def get_vacancy(instance):
        return VacancyInConfirmedWorkerSerializer(instance=instance.shift.vacancy).data

    @staticmethod
    def get_user(instance):
        return ConfirmedWorkerSerializer(instance=instance.applier).data

    @staticmethod
    def get_time_start(instance):
        return instance.shift.time_start

    @staticmethod
    def get_time_end(instance):
        return instance.shift.time_end

    @staticmethod
    def get_real_time_start(instance):
        return datetime_to_timestamp(instance.time_start)

    @staticmethod
    def get_real_time_end(instance):
        return datetime_to_timestamp(instance.time_end)

    class Meta:
        model = ShiftAppeal
        fields = [
            'id',
            'shift_id',
            'status',
            'time_start',
            'time_end',
            'real_time_start',
            'real_time_end',
            'fire_at',
            'notify_leaving',
            'user',
            'vacancy',
        ]


class QRCodeSerializer(serializers.Serializer):
    qr_text = serializers.CharField()


class ConfirmedWorkerSettingsValidator(serializers.Serializer):
    notify_leaving = serializers.BooleanField()


class QRCodeCompleteSerializer(serializers.Serializer):
    qr_text = serializers.CharField()
    reason = serializers.ChoiceField(choices=choices(AppealCompleteReason), allow_null=True)
    text = serializers.CharField(allow_null=True, required=False)


class ShiftAppealCompleteSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=choices(AppealCompleteReason), allow_null=True, required=False)
    text = serializers.CharField(allow_null=True, required=False, allow_blank=True)


class ManagerAppealCancelReasonSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=choices(ManagerAppealCancelReason))
    text = serializers.CharField(allow_null=True, required=False)


class FireByManagerReasonSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=choices(FireByManagerReason))
    text = serializers.CharField(allow_null=True, required=False)


class ProlongByManagerReasonSerializer(serializers.Serializer):
    hours = serializers.IntegerField(allow_null=False)


class SecurityPassRefuseReasonSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=choices(SecurityPassRefuseReason))
    text = serializers.CharField(allow_null=True, required=False)


class ShiftConditionsSerializer(serializers.Serializer):
    shift_id = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    time_start = serializers.SerializerMethodField()
    time_end = serializers.SerializerMethodField()
    full_price = serializers.SerializerMethodField()
    tax = serializers.SerializerMethodField()
    insurance = serializers.SerializerMethodField()
    clean_price = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    vacancy = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    def get_shift_id(self, instance):
        return instance.id

    def get_date(self, instance):
        return instance.date

    def get_time_start(self, instance):
        return instance.time_start

    def get_time_end(self, instance):
        return instance.time_end

    def get_full_price(self, instance):
        return instance.full_price

    def get_tax(self, instance):
        return instance.tax

    def get_insurance(self, instance):
        return instance.insurance

    def get_clean_price(self, instance):
        return instance.clean_price

    def get_text(self, instance):
        return instance.text

    def get_vacancy(self, instance):
        return VacancyInShiftForDocumentsSerializer(instance.vacancy, many=False).data

    def get_documents(self, instance):
        return DocumentsSerializer(instance.documents, many=True).data


class PartnerConditionsSerializer(serializers.Serializer):
    partner_id = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    def get_partner_id(self, instance):
        return instance.id

    def get_documents(self, instance):
        return DocumentsSerializer(instance.documents, many=True).data


class DocumentsSerializer(serializers.Serializer):
    document = serializers.SerializerMethodField()
    is_confirmed = serializers.SerializerMethodField()

    def get_document(self, instance):
        return MediaSerializer(instance, many=False).data

    def get_is_confirmed(self, instance):
        return instance.is_confirmed


class DistributorInPartnerSerializer(DistributorsSerializer):
    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
            'description',
            'logo',
            'banner'
        ]


class PartnersSerializer(serializers.ModelSerializer):
    distributor = serializers.SerializerMethodField()

    def get_distributor(self, data):
        if data.distributor:
            return DistributorInPartnerSerializer(data.distributor).data
        return None

    class Meta:
        model = Partner
        fields = [
            'id',
            'color',
            'distributor'
        ]


class AchievementsSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    achieved_count = serializers.SerializerMethodField()

    def get_icon(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.ACHIEVEMENT_ICON.value)

    def get_completed_at(self, data):
        return datetime_to_timestamp(data.completed_at) if data.completed_at else None

    def get_achieved_count(self, data):
        return data.achieved_count

    class Meta:
        model = Achievement
        fields = [
            'id',
            'name',
            'description',
            'completed_at',
            'achieved_count',
            'icon'
        ]


class AdvertisementsSerializer(serializers.ModelSerializer):
    banner = serializers.SerializerMethodField()
    created_at = DateTimeField()

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.BANNER.value)

    class Meta:
        model = Advertisement
        fields = [
            'id',
            'title',
            'description',
            'created_at',
            'banner'
        ]


class OrdersSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()

    class Meta:
        model = Order
        fields = [
            'id',
            'description',
            'created_at',
            'email',
            'type',
            'status',
        ]


class CouponsSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()
    partner = serializers.SerializerMethodField()
    max_multiplier = serializers.SerializerMethodField()

    def get_partner(self, data):
        if data.partner:
            return PartnersSerializer(data.partner).data
        return None

    def get_max_multiplier(self, data):
        if data.bonus_balance:
            return int(data.bonus_balance / data.bonus_price)
        return 0

    class Meta:
        model = Coupon
        fields = [
            'id',
            'description',
            'discount',
            'bonus_price',
            'max_multiplier',
            'discount_terms',
            'service_description',
            'created_at',
            'partner'
        ]


class FinancesValiadator(serializers.Serializer):
    interval = serializers.ChoiceField(choices=choices(FinancesInterval))
    currency = serializers.ChoiceField(choices=choices(Currency))
    interval_name = serializers.SerializerMethodField()

    def get_interval_name(self, data):
        return FinancesInterval(data.interval).name.lower()


class OrdersValiadator(serializers.Serializer):
    type = serializers.ChoiceField(choices=choices(OrderType))
    amount = serializers.IntegerField(min_value=0)


class BuyCouponsValidator(serializers.Serializer):
    type = serializers.ChoiceField(choices=choices(OrderType))
    amount = serializers.IntegerField(min_value=0)
    coupon = serializers.IntegerField()
    email = serializers.EmailField()
    partner = serializers.IntegerField(required=False)
    terms_accepted = serializers.BooleanField()


class FinancesSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    pay_amount = serializers.SerializerMethodField()
    taxes_amount = serializers.SerializerMethodField()
    insurance_amount = serializers.SerializerMethodField()
    penalty_amount = serializers.SerializerMethodField()
    friend_reward_amount = serializers.SerializerMethodField()
    interval = serializers.SerializerMethodField()
    interval_date = DateTimeField()
    utc_offset = serializers.SerializerMethodField()

    def get_total(self, data):
        return data['total']

    def get_pay_amount(self, data):
        return data['pay_amount']

    def get_taxes_amount(self, data):
        return data['taxes_amount']

    def get_insurance_amount(self, data):
        return data['insurance_amount']

    def get_penalty_amount(self, data):
        return data['penalty_amount']

    def get_friend_reward_amount(self, data):
        return data['friend_reward_amount']

    def get_interval(self, data):
        return data['interval']

    def get_utc_offset(self, data):
        return data['utc_offset']

    class Meta:
        model = Transaction
        fields = [
            'total',
            'pay_amount',
            'taxes_amount',
            'insurance_amount',
            'penalty_amount',
            'friend_reward_amount',
            'interval',
            'interval_date',
            'utc_offset',
        ]


class InsuranceSerializer(serializers.ModelSerializer):
    time_start = DateTimeField()
    time_end = DateTimeField()
    insurance_payment_expiration = DateTimeField()
    insured_birth_date = DateTimeField()
    utc_offset = serializers.SerializerMethodField()
    is_confirmed = serializers.SerializerMethodField()

    def get_utc_offset(self, data):
        return pytz.timezone(data.timezone).utcoffset(datetime.utcnow()).total_seconds()

    def get_is_confirmed(self, data):
        return data.confirmed_at is not None

    class Meta:
        model = ShiftAppealInsurance
        exclude = [
            'appeal',
        ]
