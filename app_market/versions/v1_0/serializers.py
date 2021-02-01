from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models.functions import Distance
from django.db.models import QuerySet, Prefetch, Value, IntegerField
from django_globals import globals as g
from rest_framework import serializers

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShopsRepository
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from backend.mixins import CRUDSerializer
from backend.utils import chained_get


class DistributorSerializer(CRUDSerializer):
    repository = DistributorsRepository

    categories = serializers.SerializerMethodField()

    def get_categories(self, instance):
        return []

    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
            'description',
            'categories',
        ]


class ShopSerializer(CRUDSerializer):
    repository = ShopsRepository

    distributor = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def get_distributor(self, instance):
        return None

    def get_lon(self, instance):
        if instance.location:
            return instance.location.x
        return None

    def get_lat(self, instance):
        if instance.location:
            return instance.location.y
        return None

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'address',
            'lon',
            'lat',
            'distributor',
        ]


class ShopInVacancySerializer(serializers.ModelSerializer):
    walk_time = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = g.request.headers.get('Platform', '').lower()

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

    def get_logo(self, prefetched_data):
        file = MediaRepository.get_related_media_file(
            self.instance, prefetched_data, MediaType.LOGO.value, MediaFormat.IMAGE.value
        )

        if file:
            return MediaSerializer(file, many=False).data
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


class DistributorInVacancySerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()

    def get_logo(self, prefetched_data):
        file = MediaRepository.get_related_media_file(
            self.instance, prefetched_data, MediaType.LOGO.value, MediaFormat.IMAGE.value
        )

        if file:
            return MediaSerializer(file, many=False).data
        return None

    def get_banner(self, prefetched_data):
        file = MediaRepository.get_related_media_file(
            self.instance, prefetched_data, MediaType.BANNER.value, MediaFormat.IMAGE.value
        )

        if file:
            return MediaSerializer(file, many=False).data
        return None

    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
            'logo',
            'banner',
        ]


class VacancySerializer(CRUDSerializer):
    repository = VacanciesRepository

    is_favourite = serializers.SerializerMethodField()
    is_hot = serializers.SerializerMethodField()
    work_time = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()
    distributor = serializers.SerializerMethodField()

    def fast_related_loading(self, queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            Vacancy
            -> Shop + Media
            -> Distributor + Media
        """
        queryset = queryset.prefetch_related(
            Prefetch(
                'shop',
                #  Подгрузка магазинов и вычисление расстояния от каждого до переданной точки
                queryset=Shop.objects.annotate(  # Вычисляем расстояние, если переданы координаты
                    distance=Distance('location', point) if point else Value(None, IntegerField())
                ).prefetch_related(
                    # Подгрузка медиа для магазинов
                    Prefetch(
                        'media',
                        queryset=MediaModel.objects.filter(
                            type=MediaType.LOGO.value,
                            owner_ct_id=ContentType.objects.get_for_model(Shop).id,
                            format=MediaFormat.IMAGE.value
                        ),
                        to_attr='medias'
                    )).prefetch_related(
                    # Подгрузка торговых сетей для магазинов
                    Prefetch(
                        'distributor',
                        queryset=Distributor.objects.all().prefetch_related(
                            # Подгрузка медиа для торговых сетей
                            Prefetch(
                                'media',
                                queryset=MediaModel.objects.filter(
                                    type__in=[MediaType.LOGO.value, MediaType.BANNER.value],
                                    owner_ct_id=ContentType.objects.get_for_model(
                                        Distributor).id,
                                    format=MediaFormat.IMAGE.value
                                ),
                                to_attr='medias'
                            )
                        )
                    )
                )
            )
        )

        return queryset

    def get_is_favourite(self, vacancy):
        return False

    def get_is_hot(self, vacancy):
        return vacancy.is_hot

    def get_work_time(self, vacancy):
        return vacancy.work_time

    def get_shop(self, vacancy):
        return ShopInVacancySerializer(vacancy.shop).data

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
            'required_experience',
            'employment',
            'work_time',
            'shop',
            'distributor',
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
