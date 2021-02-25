from datetime import datetime

import pytz
from django.db.models import Avg
from rest_framework import serializers

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, UserShift, Category
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShifsRepository
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
            'required_experience',
            'employment',
            'work_time',
            'shop',
            'distributor',
            'rating'
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
