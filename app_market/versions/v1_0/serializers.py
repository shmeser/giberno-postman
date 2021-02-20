from datetime import datetime

import pytz
from rest_framework import serializers

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, UserShift
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShopsRepository, ShifsRepository
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer
from backend.utils import chained_get, datetime_to_timestamp


class DistributorSerializer(CRUDSerializer):
    repository = DistributorsRepository

    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    categories = serializers.SerializerMethodField()
    vacancies_count = serializers.SerializerMethodField()
    shops = serializers.SerializerMethodField()

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.LOGO.value)

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

    def get_categories(self, instance):
        return []

    def get_vacancies_count(self, prefetched_data):
        return chained_get(prefetched_data, 'vacancies_count')

    def get_shops(self, instance):
        return []

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
            'banner',
            'shops',
        ]


class ShopSerializer(CRUDSerializer):
    repository = ShopsRepository
    distributor = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.LOGO.value)

    def get_distributor(self, instance):
        return None

    def get_rating(self, instance):
        return None

    def get_rates_count(self, instance):
        return None

    def get_lon(self, instance):
        return instance.location.x if instance.location else None

    def get_lat(self, instance):
        return instance.location.y if instance.location else None

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'lon',
            'lat',
            'rating',
            'rates_count',
            'logo',
            'banner',
            'distributor',
        ]


class ShopInVacancySerializer(CRUDSerializer):
    """ Вложенная модель магазина в вакансии (на экране просмотра одной вакансии) """

    logo = serializers.SerializerMethodField()
    map = serializers.SerializerMethodField()

    walk_time = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.LOGO.value)

    def get_map(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.MAP.value)

    def get_walk_time(self, shop):
        if chained_get(shop, 'distance'):
            # Принимаем среднюю скорость пешеходов за 3.6км/ч = 1м/с
            # Выводим расстояние в метрах как количество секунд
            return int(shop.distance.m)
        return None

    def get_lon(self, shop):
        if shop.location:
            return shop.location.x
        return None

    def get_lat(self, shop):
        if shop.location:
            return shop.location.y
        return None

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'rating',
            'rates_count',
            'walk_time',
            'lon',
            'lat',
            'logo',
            'map',
        ]


class ShopsInVacanciesSerializer(CRUDSerializer):
    """ Вложенная модель магазина в списке вакансий """
    walk_time = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

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
            'logo',
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

    def get_is_favourite(self, prefetched_data):
        # TODO брать из app_feedback из модели Like
        return False

    def get_utc_offset(self, vacancy):
        return pytz.timezone(vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds()

    def get_is_hot(self, vacancy):
        return vacancy.is_hot

    def get_free_count(self, vacancy):
        return vacancy.free_count

    def get_work_time(self, vacancy):
        return vacancy.work_time

    def get_shop(self, vacancy):
        return ShopsInVacanciesSerializer(vacancy.shop).data

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
            'required_experience',
            'employment',
            'work_time',
            'shop',
            'distributor',
        ]


class VacancySerializer(VacanciesSerializer):
    created_at = DateTimeField()
    banner = serializers.SerializerMethodField()
    utc_offset = serializers.SerializerMethodField()

    def get_banner(self, prefetched_data):
        return MediaController(self.instance).get_related_image(prefetched_data, MediaType.BANNER.value)

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
            'distributor',
        ]


class ShiftsSerializer(CRUDSerializer):
    repository = ShifsRepository

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


class UserShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserShift
        fields = '__all__'


class QRCodeSerializer(serializers.Serializer):
    qr_code = serializers.CharField()
