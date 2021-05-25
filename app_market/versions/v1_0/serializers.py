from datetime import datetime

import pytz
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Sum
from rest_framework import serializers

from app_market.enums import ShiftAppealStatus
from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, UserShift, Category, ShiftAppeal
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShiftsRepository
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.controllers import MediaController
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.models import UserProfile
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer
from backend.utils import chained_get, datetime_to_timestamp, timestamp_to_datetime


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
        # TODO добавить загрузку файла карт с гугла после получения платного аккаунта
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

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'address',
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
        return vacancy.likes.filter(owner_id=self.me.id, target_id=vacancy.id, deleted=False).exists()

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

    def get_shop(self, vacancy):
        return ShopInVacancySerializer(vacancy.shop).data

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
            return queryset.aggregate(Sum('employees_count')).get('employees_count__sum', 0)
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
        return ShiftAppeal.objects.filter(
            shift__vacancy=instance,
            shift_active_date=self.context.get('current_date')
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
        fields = ['id', 'status', 'shift_active_date', 'time_start', 'time_end', 'created_at', 'shift', 'vacancy']


class ShiftsWithAppealsSerializer(CRUDSerializer):
    appliers = serializers.SerializerMethodField()

    def get_appliers(self, instance):
        appliers = [appeal.applier for appeal in
                    instance.appeals.filter(shift_active_date=self.context.get('current_date'))]
        return UserProfileInVacanciesForManagerSerializer(instance=appliers, many=True).data

    confirmed_appliers = serializers.SerializerMethodField()

    def get_confirmed_appliers(self, instance):
        filtered_by_date = instance.appeals.filter(
            status=ShiftAppealStatus.CONFIRMED,
            shift_active_date=self.context.get('current_date')
        )
        appliers = [appeal.applier for appeal in filtered_by_date]
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
    required_docs = serializers.SerializerMethodField()
    work_experience = serializers.SerializerMethodField()

    def get_applier(self, instance):
        return ApplierSerializer(instance.applier, many=False).data

    def get_required_docs(self, instance):
        return []

    def get_work_experience(self, instance):
        return []

    class Meta:
        model = ShiftAppeal
        fields = ['id', 'status', 'applier', 'required_docs', 'work_experience']


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
            'date_start',
            'date_end',
            'time_start',
            'time_end',
            'active_today',
            'active_dates'
        ]


class ShiftForManagersSerializer(serializers.ModelSerializer):
    all_appeals_count = serializers.SerializerMethodField()
    confirmed_appeals_count = serializers.SerializerMethodField()
    vacancy_title = serializers.SerializerMethodField()

    def get_all_appeals_count(self, data):
        return data.all_appeals_count

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
            'all_appeals_count',
            'confirmed_appeals_count',
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


class VacancyIsUserShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = ['title', 'timezone', 'available_from']


class UserShiftSerializer(serializers.ModelSerializer):
    vacancy = serializers.SerializerMethodField()

    @staticmethod
    def get_vacancy(instance):
        return VacancyIsUserShiftSerializer(instance=instance.shift.vacancy).data

    class Meta:
        model = UserShift
        exclude = ['created_at', 'updated_at', 'deleted']


class QRCodeSerializer(serializers.Serializer):
    qr_data = serializers.JSONField()


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
        return ShiftDocumentsSerializer(instance.documents, many=True).data


class ShiftDocumentsSerializer(serializers.Serializer):
    document = serializers.SerializerMethodField()
    is_confirmed = serializers.SerializerMethodField()

    def get_document(self, instance):
        return MediaSerializer(instance, many=False).data

    def get_is_confirmed(self, instance):
        return instance.is_confirmed
