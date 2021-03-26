from datetime import datetime

import pytz
from django.db.models import Avg
from rest_framework import serializers

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, UserShift, Category, ShiftAppeal
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShiftsRepository
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer
from backend.utils import chained_get, datetime_to_timestamp


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
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.LOGO.value)

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

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
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.LOGO.value)

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
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'walk_time',
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
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.MAP.value)

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'walk_time',
            'rating',
            'rates_count',
            'lon',
            'lat',
            'logo',
            'map',
        ]


class DistributorInVacancySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.LOGO.value)

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

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
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

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


class VacanciesForManagerSerializer(CRUDSerializer):
    banner = serializers.SerializerMethodField()

    @staticmethod
    def get_banner(instance):
        return MediaController(instance).get_related_image(instance, MediaType.BANNER.value)

    free_count = serializers.SerializerMethodField()

    @staticmethod
    def get_free_count(instance):
        return instance.free_count

    appliers_count = serializers.SerializerMethodField()

    @staticmethod
    def get_appliers_count(instance):
        return instance.appliers_count

    appliers = serializers.SerializerMethodField()

    @staticmethod
    def get_appliers(instance):
        return ShiftAppealsSerializer(instance=instance.first_three_appliers, many=True).data

    class Meta:
        model = Vacancy
        fields = '__all__'


class ShiftAppealsSerializer(CRUDSerializer):
    class Meta:
        model = ShiftAppeal
        fields = '__all__'


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
        fields = '__all__'


class QRCodeSerializer(serializers.Serializer):
    qr_data = serializers.JSONField()
