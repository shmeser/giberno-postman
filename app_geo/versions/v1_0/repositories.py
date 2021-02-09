from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Prefetch, F

from app_geo.models import Language, Country, City, Region
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from giberno.settings import NEAREST_POINT_DISTANCE_MAX


class LanguagesRepository(MasterRepository):
    model = Language

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )


class CountriesRepository(MasterRepository):
    model = Country

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    @staticmethod
    def fast_related_loading(queryset):
        country_ct = ContentType.objects.get_for_model(Country).id
        queryset = queryset.prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    owner_ct_id=country_ct,
                    type=MediaType.FLAG.value,
                    format=MediaFormat.IMAGE.value,
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем флаги в поле medias
            )
        )

        return queryset


class RegionsRepository(MasterRepository):
    model = Region

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )


class CitiesRepository(MasterRepository):
    model = City

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def geocode(self, point):
        # Если входит в территорию нескольких зон, то сортируем по убыванию численности населения - нулы в конце
        within_boundary = self.model.objects.filter(boundary__covers=point).order_by(
            F('population').desc(nulls_last=True)
        )
        if not within_boundary:
            # Если не входит в зоны, то ищем ближайшие точки до которых менее NEAREST_POINT_DISTANCE_MAX метров
            # Сортировка по возрастанию удаленности
            near_point = self.model.objects.annotate(distance=Distance('position', point)).filter(
                distance__lte=NEAREST_POINT_DISTANCE_MAX).order_by('distance')
            return near_point
        return within_boundary

    @staticmethod
    def fast_related_loading(queryset):
        queryset = queryset.select_related('country', 'region')
        return queryset

    def get_suggestions(self, search, paginator=None):
        records = self.model.objects.exclude(deleted=True).annotate(
            similarity=TrigramSimilarity('native', search),
        ).filter(native__trigram_similar=search).order_by('-similarity')

        records = records.only('native').distinct().values_list('native', flat=True)
        return records[paginator.offset:paginator.limit] if paginator else records[:100]
